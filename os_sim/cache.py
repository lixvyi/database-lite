from collections import OrderedDict
from dataclasses import dataclass
from threading import RLock
from time import monotonic
from .errors import WriteBarrierError


@dataclass
class Frame:
    page_id:int; payload:bytes; generation:int; dirty:bool=False; pin_count:int=0; page_lsn:int=0; loaded_at:float=0


class PageCache:
    """LRU/FIFO 可切换缓存；缓存数据页，目录和 WAL 由独立持久化路径管理。"""
    def __init__(self,page_file,wal,capacity=16,policy="LRU",event_limit=2000):
        if policy not in ("LRU","FIFO"):raise ValueError("policy must be LRU or FIFO")
        self.file,self.wal,self.capacity,self.policy=page_file,wal,capacity,policy;self.frames=OrderedDict();self.lock=RLock()
        self.hits=self.misses=self.evictions=self.flushes=0;self.events=[];self.event_limit=event_limit
    def _log(self,event,page_id,**extra):
        self.events.append({"time":round(monotonic(),6),"event":event,"page_id":page_id,**extra});self.events=self.events[-self.event_limit:]
    def fetch(self,page_id,pin=True):
        with self.lock:
            if page_id in self.frames:
                self.hits+=1;frame=self.frames[page_id]
                if self.policy=="LRU":self.frames.move_to_end(page_id)
                self._log("hit",page_id)
            else:
                self.misses+=1
                if len(self.frames)>=self.capacity:self._evict()
                payload,generation=self.file.read_page(page_id);frame=Frame(page_id,payload,generation,loaded_at=monotonic());self.frames[page_id]=frame;self._log("miss",page_id)
            if pin:frame.pin_count+=1
            return frame
    def unpin(self,page_id):
        with self.lock:self.frames[page_id].pin_count=max(0,self.frames[page_id].pin_count-1)
    def update(self,page_id,payload):
        with self.lock:
            frame=self.fetch(page_id);generation=frame.generation+1;lsn=self.wal.append_page(page_id,generation,payload)
            frame.payload,frame.generation,frame.dirty,frame.page_lsn=payload,generation,True,lsn;self.unpin(page_id);self._log("dirty",page_id,lsn=lsn);return lsn
    def _flush(self,frame):
        if frame.page_lsn>self.wal.durable_lsn:raise WriteBarrierError(f"WAL {frame.page_lsn} is not durable")
        self.file.write_page(frame.page_id,frame.payload,frame.generation);frame.dirty=False;self.flushes+=1;self._log("flush",frame.page_id,lsn=frame.page_lsn)
    def flush_page(self,page_id):
        with self.lock:
            frame=self.frames.get(page_id)
            if frame and frame.dirty:self._flush(frame)
    def flush_all(self):
        with self.lock:
            for frame in self.frames.values():
                if frame.dirty:self._flush(frame)
    def _evict(self):
        for page_id,frame in list(self.frames.items()):
            if frame.pin_count==0:
                if frame.dirty:self._flush(frame)
                del self.frames[page_id];self.evictions+=1;self._log("evict",page_id);return
        raise RuntimeError("cache pressure: all frames are pinned")
    def stats(self):
        total=self.hits+self.misses
        return {"policy":self.policy,"capacity":self.capacity,"resident":len(self.frames),"dirty":sum(f.dirty for f in self.frames.values()),"hits":self.hits,"misses":self.misses,"hit_rate":self.hits/total if total else 0.0,"evictions":self.evictions,"flushes":self.flushes,"disk_reads":self.file.reads,"disk_writes":self.file.writes}
