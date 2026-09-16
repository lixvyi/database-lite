from collections import OrderedDict
from contextlib import contextmanager
from threading import RLock

class BufferPool:
    """固定容量 LRU 缓冲池；pin 防止正在使用的页被淘汰。"""

    def __init__(self, disk, capacity=16):
        """初始化对象状态和依赖。"""
        self.disk, self.capacity = (disk, capacity)
        self.frames = OrderedDict()
        self.pins = {}
        self.hits = self.misses = self.evictions = 0
        self.lock = RLock()

    def fetch(self, pid):
        """从缓存或磁盘取得指定页面。"""
        with self.lock:
            if pid in self.frames:
                self.hits += 1
                page = self.frames.pop(pid)
                self.frames[pid] = page
            else:
                self.misses += 1
                if len(self.frames) >= self.capacity:
                    self.evict()
                page = self.disk.read(pid)
                self.frames[pid] = page
            self.pins[pid] = self.pins.get(pid, 0) + 1
            return page

    def unpin(self, pid, dirty=False):
        """减少页面固定计数并记录脏状态。"""
        with self.lock:
            if dirty:
                self.frames[pid].dirty = True
            self.pins[pid] = max(0, self.pins.get(pid, 0) - 1)

    @contextmanager
    def page(self, pid):
        """以上下文方式固定并访问缓存页。"""
        page = self.fetch(pid)
        try:
            yield page
        finally:
            self.unpin(pid, page.dirty)

    def new_page(self):
        """创建并固定一个新缓存页。"""
        with self.lock:
            if len(self.frames) >= self.capacity:
                self.evict()
            page = self.disk.allocate()
            self.frames[page.page_id] = page
            self.pins[page.page_id] = 1
            return page

    def evict(self):
        """完成evict相关处理。"""
        for pid, page in list(self.frames.items()):
            if self.pins.get(pid, 0) == 0:
                if page.dirty:
                    self.disk.write(page)
                del self.frames[pid]
                self.pins.pop(pid, None)
                self.evictions += 1
                return
        raise RuntimeError('all buffer pages are pinned')

    def flush_all(self):
        """把全部脏页安全写回磁盘。"""
        with self.lock:
            for page in self.frames.values():
                if page.dirty:
                    self.disk.write(page)

    def stats(self):
        """返回缓存和存储运行统计。"""
        return {'capacity': self.capacity, 'resident': len(self.frames), 'hits': self.hits, 'misses': self.misses, 'evictions': self.evictions, 'disk_reads': self.disk.io_reads, 'disk_writes': self.disk.io_writes}
