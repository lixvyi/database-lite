from dataclasses import asdict, dataclass
import json
from pathlib import Path
from .errors import SemanticError
import struct
from .storage.page import MAGIC as PAGE_MAGIC, NO_PAGE, SlottedPage
from .storage.record import RecordCodec


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
    def exists(self,name):return name.lower() in self.tables
    def table(self,name,location=None):
        t=self.tables.get(name.lower())
        if not t: raise SemanticError(f"table '{name}' does not exist",location)
        return t
    def column(self,table,name,location=None):
        col=next((c for c in table.columns if c.name.lower()==name.lower()),None)
        if not col: raise SemanticError(f"column '{name}' does not exist in table '{table.name}'",location)
        return col


class PagedCatalog:
    """物理页 0 起始的特殊系统表；目录行使用与用户表相同的槽页和行编码。"""
    LEGACY_MAGIC=b"CAT1";LEGACY_HEADER=struct.Struct("<4sI")
    SYSTEM_SCHEMA=TableSchema("pg_catalog",[
        ColumnSchema("table_name","VARCHAR",128),ColumnSchema("column_name","VARCHAR",128),
        ColumnSchema("data_type","VARCHAR",16),ColumnSchema("length","INT"),
        ColumnSchema("column_order","INT"),ColumnSchema("first_page","INT")])
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
        if raw[:4]==self.LEGACY_MAGIC:
            _,size=self.LEGACY_HEADER.unpack_from(raw);data=json.loads(raw[self.LEGACY_HEADER.size:self.LEGACY_HEADER.size+size].decode("utf-8"))
            self.tables={n:TableSchema(n,[ColumnSchema(**c) for c in t["columns"]],t.get("first_page")) for n,t in data.items()};self.save();return
        if raw[:4]!=PAGE_MAGIC:self.tables={};self.save();return
        grouped={}
        for row in self._stored_rows():
            grouped.setdefault(row["table_name"],[]).append(row)
        self.tables={}
        for name,rows in grouped.items():
            rows.sort(key=lambda row:row["column_order"])
            columns=[ColumnSchema(row["column_name"],row["data_type"],row["length"]) for row in rows]
            self.tables[name.lower()]=TableSchema(name,columns,rows[0]["first_page"])
    def save(self):
        old_pages=self._catalog_pages()
        pages=[SlottedPage(old_pages[0])]
        for row in self.rows():
            payload=RecordCodec.encode(self.SYSTEM_SCHEMA,row)
            slot=pages[-1].insert(payload)
            if slot is None:
                page_id=old_pages[len(pages)] if len(pages)<len(old_pages) else self.store.allocate_page()
                pages[-1].next_page=page_id;pages.append(SlottedPage(page_id))
                if pages[-1].insert(payload) is None:raise SemanticError("one system catalog row is larger than one page")
        for page in pages:self.store.write_page(page.page_id,bytes(page.data))
        for page_id in old_pages[len(pages):]:self.store.release_page(page_id)
    def create_table(self,schema):
        key=schema.name.lower()
        if key in self.tables or key=="pg_catalog":raise SemanticError(f"table '{schema.name}' already exists or is reserved")
        self.tables[key]=schema;self.save()
    def exists(self,name):return name.lower()=="pg_catalog" or name.lower() in self.tables
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
        return [{"table_name":t.name,"column_name":c.name,"data_type":c.data_type,"length":c.length,
                 "column_order":i,"first_page":t.first_page}
                for t in self.tables.values() for i,c in enumerate(t.columns)]
    def _catalog_pages(self):
        raw=self.store.read_page(0)
        if raw[:4]!=PAGE_MAGIC:return [0]
        pages=[];page_id=0
        while page_id!=NO_PAGE:
            if page_id in pages:raise RuntimeError("system catalog page chain contains a cycle")
            pages.append(page_id);page=SlottedPage(page_id,self.store.read_page(page_id));page_id=page.next_page
        return pages
    def _stored_rows(self):
        for page_id in self._catalog_pages():
            page=SlottedPage(page_id,self.store.read_page(page_id))
            for _,payload in page.records():yield RecordCodec.decode(self.SYSTEM_SCHEMA,payload)
