from contextlib import contextmanager
from .page import SlottedPage

class OSBufferAdapter:
    """把数据库 SlottedPage 接到独立 StorageService，执行器不再直接访问文件。"""

    def __init__(self, store):
        """初始化对象状态和依赖。"""
        self.store = store
        self.pending = {}

    def prefetch(self, page_id):
        """完成prefetch相关处理。"""
        if page_id is not None:
            self.store.prefetch_page(page_id)

    @contextmanager
    def page(self, page_id):
        """以上下文方式固定并访问缓存页。"""
        page = SlottedPage(page_id, self.store.read_page(page_id))
        try:
            yield page
        finally:
            if page.dirty:
                self.store.write_page(page_id, bytes(page.data))

    def new_page(self):
        """创建并固定一个新缓存页。"""
        page_id = self.store.allocate_page()
        page = SlottedPage(page_id)
        self.pending[page_id] = page
        return page

    def new_table_page(self, table_name):
        """完成new table page相关处理。"""
        page_id = self.store.append_table_page(table_name)
        page = SlottedPage(page_id)
        self.pending[page_id] = page
        return page

    def unpin(self, page_id, dirty=False):
        """减少页面固定计数并记录脏状态。"""
        page = self.pending.pop(page_id, None)
        if page is not None and (dirty or page.dirty):
            self.store.write_page(page_id, bytes(page.data))

    def discard_page(self, page_id):
        """丢弃未投入使用的新页面。"""
        self.pending.pop(page_id, None)
        self.store.release_page(page_id)

    def flush_all(self):
        """把全部脏页安全写回磁盘。"""
        self.store.checkpoint()

    def stats(self):
        """返回缓存和存储运行统计。"""
        return self.store.stats()
