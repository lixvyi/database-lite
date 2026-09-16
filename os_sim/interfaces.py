from typing import Protocol

class PageStore(Protocol):
    """数据库模块只依赖稳定页接口，不依赖文件、缓存或 WAL 实现细节。"""

    def allocate_page(self) -> int:
        """分配并返回一个可用物理页。"""
        ...

    def release_page(self, page_id: int) -> None:
        """释放指定物理页供后续复用。"""
        ...

    def read_page(self, page_id: int) -> bytes:
        """读取指定页的完整内容。"""
        ...

    def write_page(self, page_id: int, payload: bytes) -> int:
        """写入指定页的完整内容。"""
        ...

    def checkpoint(self) -> dict:
        """刷新脏页并推进检查点。"""
        ...

    def stats(self) -> dict:
        """返回缓存和存储运行统计。"""
        ...
