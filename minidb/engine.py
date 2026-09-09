from copy import deepcopy
from pathlib import Path
from .ast import CreateTableStmt
from .catalog import ColumnSchema,PagedCatalog,TableSchema
from .execution import Executor
from .lexer import Lexer
from .optimizer import Optimizer
from .parser import Parser
from .plan import PlanBuilder
from .semantic import SemanticAnalyzer
from .storage import RecordCodec
from .storage.os_adapter import OSBufferAdapter
from os_sim import StorageService


class Database:
    """SQL → Token → AST → Semantic → Plan → Optimize → Execute → Page/Disk。"""
    def __init__(self,directory="minidb_data",buffer_pages=16):
        root=Path(directory);root.mkdir(parents=True,exist_ok=True)
        self.store=StorageService(root/"storage",buffer_pages,"LRU",dirty_ratio=.75)
        self.catalog=PagedCatalog(self.store);self.buffer=OSBufferAdapter(self.store);self.semantic=SemanticAnalyzer(self.catalog)
        self.builder=PlanBuilder();self.optimizer=Optimizer();self.executor=Executor(self.catalog,self.buffer,RecordCodec)
    def compile(self,sql):
        token_stream=Lexer(sql).tokenize();statements=Parser(sql).parse_all();compiled=[]
        working=object.__new__(PagedCatalog);working.tables=deepcopy(self.catalog.tables);semantic=SemanticAnalyzer(working)
        for index,ast in enumerate(statements):
            semantic.analyze(ast);before=self.builder.build(ast);after=self.optimizer.optimize(before)
            end=statements[index+1].location.offset if index+1<len(statements) else len(sql)+1
            tokens=[t.to_dict() for t in token_stream if ast.location.offset<=t.location.offset<end]
            compiled.append({"tokens":tokens,"ast":ast,"before":before,"after":after})
            if isinstance(ast,CreateTableStmt):
                working.tables[ast.table.lower()]=TableSchema(ast.table,[ColumnSchema(c.name,c.data_type,c.length) for c in ast.columns])
        return compiled
    def execute(self,sql):
        results=[]
        for ast in Parser(sql).parse_all():
            self.semantic.analyze(ast);before=self.builder.build(ast);after=self.optimizer.optimize(before)
            results.append(self.executor.run(after))
        self.buffer.flush_all();return results
    def inspect(self,sql):
        out=[]
        for x in self.compile(sql):out.append({"tokens":x["tokens"],"ast":x["ast"].to_dict(),"semantic":"passed","plan_before":x["before"].format(),"plan_after":x["after"].format()})
        return out
    def stats(self):return self.store.stats()
    def close(self):self.store.close()
