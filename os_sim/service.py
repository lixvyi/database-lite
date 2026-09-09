from pathlib import Path
from .cache import PageCache
from .errors import InvalidPage
from .page_file import PAYLOAD_SIZE,PageFile
from .wal import WriteAheadLog


class StorageService:
    """独立 OS 仿真实体：统一暴露页服务，内部组合文件、WAL 与内存缓存。"""
    def __init__(self,directory,cache_pages=16,policy="LRU",dirty_ratio=0.6):
        self.root=Path(directory);self.file=PageFile(self.root);self.wal=WriteAheadLog(self.root/"redo.wal")
        self.cache=PageCache(self.file,self.wal,cache_pages,policy);self.dirty_ratio=dirty_ratio;self.recovered_pages=self._recover()
    def _recover(self):
        recovered=0
        for record in self.wal.records():
            if record["lsn"]<=self.file.checkpoint_lsn:continue
            import base64
            payload=base64.b64decode(record["payload"])
            if len(payload)!=PAYLOAD_SIZE:continue  # v1 WAL 的 4076B after-image 已由页文件迁移处理
            try:_,generation=self.file.read_page(record["page_id"])
            except InvalidPage:continue
            if generation<record["generation"]:
                self.file.write_page(record["page_id"],payload,record["generation"]);recovered+=1
        if recovered:self.file.set_checkpoint(self.wal.durable_lsn)
        return recovered
    def allocate_page(self):return self.file.allocate_page()
    def release_page(self,page_id):
        frame=self.cache.frames.get(page_id)
        if frame and frame.pin_count:raise RuntimeError("cannot release a pinned page")
        self.cache.frames.pop(page_id,None);self.file.release_page(page_id)
    def read_page(self,page_id):
        frame=self.cache.fetch(page_id)
        try:return frame.payload
        finally:self.cache.unpin(page_id)
    def write_page(self,page_id,payload):
        if len(payload)!=PAYLOAD_SIZE:raise ValueError(f"payload must be exactly {PAYLOAD_SIZE} bytes")
        lsn=self.cache.update(page_id,payload)
        if self.cache.capacity and self.cache.stats()["dirty"]/self.cache.capacity>=self.dirty_ratio:self.flush_due()
        return lsn
    def flush_due(self,max_pages=None):
        dirty=[f for f in self.cache.frames.values() if f.dirty and f.pin_count==0]
        dirty.sort(key=lambda f:f.page_lsn)
        for frame in dirty[:max_pages]:self.cache.flush_page(frame.page_id)
        return len(dirty[:max_pages])
    def checkpoint(self):
        self.cache.flush_all();self.file.set_checkpoint(self.wal.durable_lsn)
        return {"checkpoint_lsn":self.file.checkpoint_lsn,"flushed_pages":self.cache.flushes}
    def stats(self):return {**self.cache.stats(),"wal_durable_lsn":self.wal.durable_lsn,"checkpoint_lsn":self.file.checkpoint_lsn,"recovered_pages":self.recovered_pages,"allocated_pages":sum(self.file.control["allocated"]),"total_pages":self.file.control["page_count"]}
    def page_directory(self):return self.file.page_directory()
    def close(self,clean=True):
        if clean:self.checkpoint()
