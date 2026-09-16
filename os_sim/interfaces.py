"""
操作系统子系统对数据库暴露的稳定页接口协议。

功能：
- 约束数据库模块只依赖页服务抽象，而不直接依赖底层文件、缓存或 WAL 实现细节。
- 规定分配页、释放页、读写页、checkpoint 和状态统计等核心能力。

对应需求文档：
- 第 3 节“总体架构（建议）”中的 Storage API。
- 第 6.1 节“必备 API 列表”。
- 第 7.1 节“数据库如何使用本子系统（对接约束）”。
"""
from typing import Protocol

class PageStore(Protocol):
    """数据库模块只依赖稳定页接口，不依赖文件、缓存或 WAL 实现细节。"""

    def allocate_page(self) -> int:
        """分配并返回一个可用物理页。"""
        ...

    def free_page(self, page_id: int) -> None:
        """完成free page相关处理。"""
        ...

    def release_page(self, page_id: int) -> None:
        """释放指定物理页供后续复用。"""
        ...

    def get_page(self, page_id: int) -> bytes:
        """完成get page相关处理。"""
        ...

    def read_page(self, page_id: int) -> bytes:
        """读取指定页的完整内容。"""
        ...

    def write_page(self, page_id: int, payload: bytes) -> int:
        """写入指定页的完整内容。"""
        ...

    def flush_page(self, page_id: int) -> None:
        """把指定脏页安全写回磁盘。"""
        ...

    def flush_all(self) -> dict:
        """把全部脏页安全写回磁盘。"""
        ...

    def get_table_pages(self, table_name: str) -> list[int]:
        """完成get table pages相关处理。"""
        ...

    def append_table_page(self, table_name: str) -> int:
        """完成append table page相关处理。"""
        ...

    def checkpoint(self) -> dict:
        """刷新脏页并推进检查点。"""
        ...

    def stats(self) -> dict:
        """返回缓存和存储运行统计。"""
        ...
