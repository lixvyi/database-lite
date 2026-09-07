from dataclasses import asdict, dataclass
import json
from pathlib import Path
from .errors import SemanticError
import struct


@dataclass
class ColumnSchema:
    name: str; data_type: str; length: int | None = None

@dataclass
class TableSchema:
    name: str; columns: list[ColumnSchema]; first_page: int | None = None


class Catalog:
    """编译器符号表与存储目录：表名 -> 列定义 + 物理首页号。"""
    def __init__(self, path: Path): self.path, self.tables = path, {}; self.load()
    def load(self):
        if self.path.exists():
            raw=json.loads(self.path.read_text(encoding="utf-8"))
            self.tables={n:TableSchema(n,[ColumnSchema(**c) for c in t["columns"]],t.get("first_page")) for n,t in raw.items()}
    def save(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.path.write_text(json.dumps({n:asdict(t) for n,t in self.tables.items()},ensure_ascii=False,indent=2),encoding="utf-8")
    def create_table(self, schema):
        key=schema.name.lower()
        if key in self.tables: raise SemanticError(f"table '{schema.name}' already exists")
        self.tables[key]=schema; self.save()
    def table(self,name,location=None):
        t=self.tables.get(name.lower())
        if not t: raise SemanticError(f"table '{name}' does not exist",location)
        return t
    def column(self,table,name,location=None):
        col=next((c for c in table.columns if c.name.lower()==name.lower()),None)
        if not col: raise SemanticError(f"column '{name}' does not exist in table '{table.name}'",location)
        return col


class PagedCatalog:
    """保留物理页 0 上的特殊系统表；所有元数据与用户数据共用页服务。"""
    MAGIC=b"CAT1";HEADER=struct.Struct("<4sI")
    SYSTEM_SCHEMA=TableSchema("pg_catalog",[
        ColumnSchema("table_name","VARCHAR",128),ColumnSchema("column_name","VARCHAR",128),
        ColumnSchema("data_type","VARCHAR",16),ColumnSchema("length","INT"),ColumnSchema("first_page","INT")])
    def __init__(self,page_store):
        self.store=page_store;self.page_id=self._ensure_page();self.tables={};self.load()
    def _ensure_page(self):
        allocated=[p["page_id"] for p in self.store.page_directory() if p["allocated"]]
        if not allocated:
            page_id=self.store.allocate_page()
            if page_id!=0:raise RuntimeError("catalog bootstrap page must be page 0")
            return page_id
        if 0 not in allocated:raise RuntimeError("reserved catalog page 0 is missing")
        return 0
    def load(self):
        raw=self.store.read_page(self.page_id)
        if raw[:4]!=self.MAGIC:self.tables={};self.save();return
        _,size=self.HEADER.unpack_from(raw);data=json.loads(raw[self.HEADER.size:self.HEADER.size+size].decode("utf-8"))
        self.tables={n:TableSchema(n,[ColumnSchema(**c) for c in t["columns"]],t.get("first_page")) for n,t in data.items()}
    def save(self):
        encoded=json.dumps({n:asdict(t) for n,t in self.tables.items()},ensure_ascii=False,separators=(",",":")).encode("utf-8")
        if self.HEADER.size+len(encoded)>4096:raise SemanticError("system catalog page is full")
        self.store.write_page(self.page_id,self.HEADER.pack(self.MAGIC,len(encoded))+encoded+bytes(4096-self.HEADER.size-len(encoded)))
    def create_table(self,schema):
        key=schema.name.lower()
        if key in self.tables or key=="pg_catalog":raise SemanticError(f"table '{schema.name}' already exists or is reserved")
        self.tables[key]=schema;self.save()
    def table(self,name,location=None):
        if name.lower()=="pg_catalog":return self.SYSTEM_SCHEMA
        table=self.tables.get(name.lower())
        if not table:raise SemanticError(f"table '{name}' does not exist",location)
        return table
    def column(self,table,name,location=None):
        col=next((c for c in table.columns if c.name.lower()==name.lower()),None)
        if not col:raise SemanticError(f"column '{name}' does not exist in table '{table.name}'",location)
        return col
    def rows(self):
        return [{"table_name":t.name,"column_name":c.name,"data_type":c.data_type,"length":c.length,"first_page":t.first_page} for t in self.tables.values() for c in t.columns]
