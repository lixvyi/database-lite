import struct
from ..errors import StorageError
PAGE_SIZE = 4096
MAGIC = b'SYP1'
HEADER = struct.Struct('<4sIHHHI')
SLOT = struct.Struct('<HH')
NO_PAGE = 4294967295

class SlottedPage:
    """4KB 变长记录页：页头从前增长，记录体从后向前增长。"""

    def __init__(self, page_id: int, data: bytes | None=None):
        """初始化对象状态和依赖。"""
        if data is not None and len(data) != PAGE_SIZE:
            raise StorageError(f'page {page_id} must be exactly {PAGE_SIZE} bytes')
        self.data = bytearray(data if data is not None else bytes(PAGE_SIZE))
        if data is not None:
            magic, pid, count, start, end, _ = HEADER.unpack_from(self.data)
            if magic != MAGIC or pid != page_id:
                raise StorageError(f'invalid page {page_id}')
            if start != HEADER.size + count * SLOT.size or not HEADER.size <= start <= end <= PAGE_SIZE:
                raise StorageError(f'invalid page layout {page_id}')
        else:
            HEADER.pack_into(self.data, 0, MAGIC, page_id, 0, HEADER.size, PAGE_SIZE, NO_PAGE)
        self.page_id = page_id
        self.dirty = False

    def meta(self):
        """完成meta相关处理。"""
        return HEADER.unpack_from(self.data)

    @property
    def next_page(self):
        """完成next page相关处理。"""
        return self.meta()[5]

    @next_page.setter
    def next_page(self, value):
        """完成next page相关处理。"""
        m = list(self.meta())
        m[5] = value
        HEADER.pack_into(self.data, 0, *m)
        self.dirty = True

    def free_space(self):
        """完成free space相关处理。"""
        _, _, _, start, end, _ = self.meta()
        return end - start

    def insert(self, payload: bytes):
        """解析INSERT语句。"""
        magic, pid, count, start, end, nxt = self.meta()
        if len(payload) + SLOT.size > self.free_space():
            return None
        end -= len(payload)
        self.data[end:end + len(payload)] = payload
        SLOT.pack_into(self.data, start, end, len(payload))
        HEADER.pack_into(self.data, 0, magic, pid, count + 1, start + SLOT.size, end, nxt)
        self.dirty = True
        return count

    def read(self, slot):
        """完成read相关处理。"""
        _, _, count, _, _, _ = self.meta()
        if slot < 0 or slot >= count:
            raise StorageError(f'slot {slot} outside page {self.page_id}')
        off, length = SLOT.unpack_from(self.data, HEADER.size + slot * SLOT.size)
        if length and (off < self.meta()[4] or off + length > PAGE_SIZE):
            raise StorageError(f'invalid slot {slot} in page {self.page_id}')
        return None if length == 0 else bytes(self.data[off:off + length])

    def delete(self, slot):
        """解析DELETE语句。"""
        payload = self.read(slot)
        if payload is None:
            return False
        off, _ = SLOT.unpack_from(self.data, HEADER.size + slot * SLOT.size)
        SLOT.pack_into(self.data, HEADER.size + slot * SLOT.size, off, 0)
        self.dirty = True
        return True

    def update(self, slot, payload: bytes):
        """能在本页容纳时更新槽指针；旧记录空间留待后续页压缩回收。"""
        old = self.read(slot)
        if old is None:
            return False
        slot_pos = HEADER.size + slot * SLOT.size
        off, length = SLOT.unpack_from(self.data, slot_pos)
        if len(payload) <= length:
            self.data[off:off + len(payload)] = payload
            SLOT.pack_into(self.data, slot_pos, off, len(payload))
            self.dirty = True
            return True
        magic, pid, count, start, end, nxt = self.meta()
        if len(payload) > end - start:
            return False
        end -= len(payload)
        self.data[end:end + len(payload)] = payload
        SLOT.pack_into(self.data, slot_pos, end, len(payload))
        HEADER.pack_into(self.data, 0, magic, pid, count, start, end, nxt)
        self.dirty = True
        return True

    def records(self):
        """遍历页面中的有效槽记录。"""
        count = self.meta()[2]
        for slot in range(count):
            value = self.read(slot)
            if value is not None:
                yield (slot, value)
