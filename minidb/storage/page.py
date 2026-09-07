import struct
from ..errors import StorageError

PAGE_SIZE=4096
MAGIC=b"SYP1"
HEADER=struct.Struct("<4sIHHHI") # magic,page_id,slots,free_start,free_end,next_page
SLOT=struct.Struct("<HH")       # offset,length; length=0 means deleted
NO_PAGE=0xFFFFFFFF


class SlottedPage:
    """4KB 变长记录页：页头从前增长，记录体从后向前增长。"""
    def __init__(self,page_id:int,data:bytes|None=None):
        self.data=bytearray(data or bytes(PAGE_SIZE))
        if data:
            magic,pid,*_=HEADER.unpack_from(self.data)
            if magic!=MAGIC or pid!=page_id:raise StorageError(f"invalid page {page_id}")
        else: HEADER.pack_into(self.data,0,MAGIC,page_id,0,HEADER.size,PAGE_SIZE,NO_PAGE)
        self.page_id=page_id; self.dirty=False
    def meta(self):return HEADER.unpack_from(self.data)
    @property
    def next_page(self):return self.meta()[5]
    @next_page.setter
    def next_page(self,value):
        m=list(self.meta());m[5]=value;HEADER.pack_into(self.data,0,*m);self.dirty=True
    def free_space(self):
        _,_,_,start,end,_=self.meta();return end-start
    def insert(self,payload:bytes):
        magic,pid,count,start,end,nxt=self.meta()
        if len(payload)+SLOT.size>self.free_space():return None
        end-=len(payload);self.data[end:end+len(payload)]=payload;SLOT.pack_into(self.data,start,end,len(payload))
        HEADER.pack_into(self.data,0,magic,pid,count+1,start+SLOT.size,end,nxt);self.dirty=True;return count
    def read(self,slot):
        _,_,count,_,_,_=self.meta()
        if slot<0 or slot>=count:raise StorageError(f"slot {slot} outside page {self.page_id}")
        off,length=SLOT.unpack_from(self.data,HEADER.size+slot*SLOT.size)
        return None if length==0 else bytes(self.data[off:off+length])
    def delete(self,slot):
        payload=self.read(slot)
        if payload is None:return False
        off,_=SLOT.unpack_from(self.data,HEADER.size+slot*SLOT.size);SLOT.pack_into(self.data,HEADER.size+slot*SLOT.size,off,0);self.dirty=True;return True
    def update(self,slot,payload:bytes):
        """能在本页容纳时更新槽指针；旧记录空间留待后续页压缩回收。"""
        old=self.read(slot)
        if old is None:return False
        slot_pos=HEADER.size+slot*SLOT.size;off,length=SLOT.unpack_from(self.data,slot_pos)
        if len(payload)<=length:
            self.data[off:off+len(payload)]=payload;SLOT.pack_into(self.data,slot_pos,off,len(payload));self.dirty=True;return True
        magic,pid,count,start,end,nxt=self.meta()
        if len(payload)>end-start:return False
        end-=len(payload);self.data[end:end+len(payload)]=payload;SLOT.pack_into(self.data,slot_pos,end,len(payload))
        HEADER.pack_into(self.data,0,magic,pid,count,start,end,nxt);self.dirty=True;return True
    def records(self):
        count=self.meta()[2]
        for slot in range(count):
            value=self.read(slot)
            if value is not None:yield slot,value
