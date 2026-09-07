from pathlib import Path
from .ast import CreateTableStmt,ExplainStmt,InsertStmt,SelectStmt,DeleteStmt,UpdateStmt
from .auth import Authorizer
from .catalog import PagedCatalog
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
        self.auth=Authorizer();self.auth.grant("admin","*",{"CREATE","INSERT","SELECT","DELETE","UPDATE"})
    def compile(self,sql):
        token_stream=Lexer(sql).tokenize();statements=Parser(sql).parse_all();compiled=[]
        for ast in statements:
            self.semantic.analyze(ast);before=self.builder.build(ast);after=self.optimizer.optimize(before)
            compiled.append({"tokens":[t.to_dict() for t in token_stream],"ast":ast,"before":before,"after":after})
        return compiled
    def execute(self,sql,user="admin"):
        results=[]
        for ast in Parser(sql).parse_all():
            self.semantic.analyze(ast);before=self.builder.build(ast);after=self.optimizer.optimize(before)
            target=ast.statement if isinstance(ast,ExplainStmt) else ast
            action="CREATE" if isinstance(target,CreateTableStmt) else "INSERT" if isinstance(target,InsertStmt) else "SELECT" if isinstance(target,SelectStmt) else "UPDATE" if isinstance(target,UpdateStmt) else "DELETE"
            table=target.table;policy=self._authorize(user,table,action,target)
            if isinstance(ast,ExplainStmt):
                results.append({"before":before.children[0].format(),"after":after.children[0].format()});continue
            results.append(self.executor.run(after,policy.row_filter if policy else None))
        self.buffer.flush_all();return results
    def inspect(self,sql):
        out=[]
        for x in self.compile(sql):out.append({"tokens":x["tokens"],"ast":x["ast"].to_dict(),"plan_before":x["before"].format(),"plan_after":x["after"].format()})
        return out
    def _authorize(self,user,table,action,stmt):
        if user=="admin":return None
        p=self.auth.policy(user,table,action)
        columns=getattr(stmt,"columns",[]) or []
        if isinstance(stmt,SelectStmt):columns=columns+[item.column for item in stmt.order_by]
        if isinstance(stmt,UpdateStmt):columns=[name for name,_ in stmt.assignments]
        if columns!=["*"]:self.auth.check_columns(p,columns)
        return p
    def stats(self):return self.store.stats()
    def close(self):self.store.close()
