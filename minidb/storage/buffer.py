from collections import OrderedDict
from contextlib import contextmanager
from threading import RLock


class BufferPool:
    """固定容量 LRU 缓冲池；pin 防止正在使用的页被淘汰。"""
    def __init__(self,disk,capacity=16):self.disk,self.capacity=disk,capacity;self.frames=OrderedDict();self.pins={};self.hits=self.misses=self.evictions=0;self.lock=RLock()
    def fetch(self,pid):
        with self.lock:
            if pid in self.frames:self.hits+=1;page=self.frames.pop(pid);self.frames[pid]=page
            else:
                self.misses+=1
                if len(self.frames)>=self.capacity:self.evict()
                page=self.disk.read(pid);self.frames[pid]=page
            self.pins[pid]=self.pins.get(pid,0)+1;return page
    def unpin(self,pid,dirty=False):
        with self.lock:
            if dirty:self.frames[pid].dirty=True
            self.pins[pid]=max(0,self.pins.get(pid,0)-1)
    @contextmanager
    def page(self,pid):
        page=self.fetch(pid)
        try:yield page
        finally:self.unpin(pid,page.dirty)
    def new_page(self):
        with self.lock:
            if len(self.frames)>=self.capacity:self.evict()
            page=self.disk.allocate();self.frames[page.page_id]=page;self.pins[page.page_id]=1;return page
    def evict(self):
        for pid,page in list(self.frames.items()):
            if self.pins.get(pid,0)==0:
                if page.dirty:self.disk.write(page)
                del self.frames[pid];self.pins.pop(pid,None);self.evictions+=1;return
        raise RuntimeError("all buffer pages are pinned")
    def flush_all(self):
        with self.lock:
            for page in self.frames.values():
                if page.dirty:self.disk.write(page)
    def stats(self):return {"capacity":self.capacity,"resident":len(self.frames),"hits":self.hits,"misses":self.misses,"evictions":self.evictions,"disk_reads":self.disk.io_reads,"disk_writes":self.disk.io_writes}
