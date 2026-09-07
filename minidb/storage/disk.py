from pathlib import Path
from threading import RLock
from .page import PAGE_SIZE,SlottedPage


class DiskManager:
    """物理页号 page_id 映射为文件偏移 page_id * PAGE_SIZE。"""
    def __init__(self,path:Path):
        self.path=path;path.parent.mkdir(parents=True,exist_ok=True);self.lock=RLock()
        if not path.exists():path.write_bytes(b"")
        self.io_reads=self.io_writes=0
    @property
    def page_count(self):return self.path.stat().st_size//PAGE_SIZE
    def allocate(self):
        with self.lock:
            pid=self.page_count;page=SlottedPage(pid);self.write(page);return page
    def read(self,pid):
        with self.lock, self.path.open("rb") as f:
            f.seek(pid*PAGE_SIZE);data=f.read(PAGE_SIZE);self.io_reads+=1
            if len(data)!=PAGE_SIZE:raise IndexError(f"page {pid} does not exist")
            return SlottedPage(pid,data)
    def write(self,page):
        with self.lock, self.path.open("r+b") as f:
            f.seek(page.page_id*PAGE_SIZE);f.write(page.data);f.flush();self.io_writes+=1;page.dirty=False
