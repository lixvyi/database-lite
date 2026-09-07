from .ast import *
from .catalog import Catalog
from .errors import SemanticError


class SemanticAnalyzer:
    def __init__(self,catalog:Catalog): self.catalog=catalog
    def analyze(self,stmt):
        if isinstance(stmt,CreateTableStmt):
            names=[c.name.lower() for c in stmt.columns]
            if len(names)!=len(set(names)): raise SemanticError("duplicate column name",stmt.location)
            return stmt
        if isinstance(stmt,ExplainStmt): self.analyze(stmt.statement); return stmt
        table=self.catalog.table(stmt.table,stmt.location)
        if table.name.lower()=="pg_catalog" and not isinstance(stmt,SelectStmt):
            raise SemanticError("system catalog 'pg_catalog' is read-only",stmt.location)
        if isinstance(stmt,InsertStmt):
            if len(stmt.columns)!=len(stmt.values): raise SemanticError("INSERT column count does not match value count",stmt.location)
            if len({c.lower() for c in stmt.columns})!=len(stmt.columns): raise SemanticError("duplicate INSERT column",stmt.location)
            for name,value in zip(stmt.columns,stmt.values):
                col=self.catalog.column(table,name,value.location); actual=self.expr(value,table)
                if actual!="NULL" and actual!=col.data_type: raise SemanticError(f"column '{name}' expects {col.data_type}, but {actual} found",value.location)
        elif isinstance(stmt,SelectStmt):
            if stmt.columns!=["*"]:
                for name in stmt.columns:self.catalog.column(table,name,stmt.location)
            for item in stmt.order_by:self.catalog.column(table,item.column,item.location)
            if stmt.where and self.expr(stmt.where,table)!="BOOL": raise SemanticError("WHERE expression must be BOOL",stmt.where.location)
        elif isinstance(stmt,DeleteStmt):
            if stmt.where and self.expr(stmt.where,table)!="BOOL": raise SemanticError("WHERE expression must be BOOL",stmt.where.location)
        elif isinstance(stmt,UpdateStmt):
            names=[name.lower() for name,_ in stmt.assignments]
            if len(names)!=len(set(names)):raise SemanticError("duplicate UPDATE column",stmt.location)
            for name,value in stmt.assignments:
                col=self.catalog.column(table,name,value.location);actual=self.expr(value,table)
                if actual!="NULL" and actual!=col.data_type:raise SemanticError(f"column '{name}' expects {col.data_type}, but {actual} found",value.location)
            if stmt.where and self.expr(stmt.where,table)!="BOOL":raise SemanticError("WHERE expression must be BOOL",stmt.where.location)
        return stmt
    def expr(self,e,table):
        if isinstance(e,LiteralExpr): typ=e.literal_type
        elif isinstance(e,IdentifierExpr): typ=self.catalog.column(table,e.name,e.location).data_type
        elif isinstance(e,UnaryExpr):
            child=self.expr(e.operand,table)
            if e.operator=="NOT" and child!="BOOL": raise SemanticError("operator 'NOT' requires BOOL",e.location)
            typ="BOOL"
        elif isinstance(e,BinaryExpr):
            left,right=self.expr(e.left,table),self.expr(e.right,table)
            if e.operator in ("AND","OR"):
                if left!="BOOL" or right!="BOOL": raise SemanticError(f"operator '{e.operator}' requires BOOL operands",e.location)
                typ="BOOL"
            elif e.operator in ("+","-","*","/"):
                if left not in ("INT","FLOAT") or right not in ("INT","FLOAT"): raise SemanticError(f"operator '{e.operator}' cannot be applied to {left} and {right}",e.location)
                typ="FLOAT" if "FLOAT" in (left,right) or e.operator=="/" else "INT"
            else:
                if left!=right and "NULL" not in (left,right): raise SemanticError(f"cannot compare {left} with {right}",e.location)
                typ="BOOL"
        else: raise SemanticError("unknown expression node",e.location)
        e.inferred_type=typ; return typ
