from dataclasses import dataclass,field
from .ast import *


@dataclass
class PlanNode:
    kind:str; args:dict=field(default_factory=dict); children:list["PlanNode"]=field(default_factory=list)
    def to_dict(self): return {"node":self.kind,**self.args,"children":[c.to_dict() for c in self.children]}
    def format(self,depth=0):
        detail=", ".join(f"{k}={v}" for k,v in self.args.items() if k not in ("predicate","values","assignments"))
        line="  "*depth+self.kind+(f"[{detail}]" if detail else "")
        return "\n".join([line]+[c.format(depth+1) for c in self.children])


def expr_text(e):
    if isinstance(e,IdentifierExpr):return e.name
    if isinstance(e,LiteralExpr):return repr(e.value)
    if isinstance(e,UnaryExpr):return f"{e.operator} ({expr_text(e.operand)})"
    if isinstance(e,BinaryExpr):return f"({expr_text(e.left)} {e.operator} {expr_text(e.right)})"
    return "?"


class PlanBuilder:
    def build(self,s):
        if isinstance(s,ExplainStmt): return PlanNode("Explain",{},[self.build(s.statement)])
        if isinstance(s,CreateTableStmt): return PlanNode("CreateTable",{"table":s.table,"columns":[(c.name,c.data_type,c.length) for c in s.columns]})
        if isinstance(s,InsertStmt): return PlanNode("Insert",{"table":s.table,"columns":s.columns,"values":s.values})
        if isinstance(s,DeleteStmt):
            scan=PlanNode("SeqScan",{"table":s.table}); child=PlanNode("Filter",{"predicate":s.where,"display":expr_text(s.where)},[scan]) if s.where else scan
            return PlanNode("Delete",{"table":s.table},[child])
        if isinstance(s,UpdateStmt):
            scan=PlanNode("SeqScan",{"table":s.table});child=PlanNode("Filter",{"predicate":s.where,"display":expr_text(s.where)},[scan]) if s.where else scan
            display=", ".join(f"{name}={expr_text(value)}" for name,value in s.assignments)
            return PlanNode("Update",{"table":s.table,"assignments":s.assignments,"set":display},[child])
        if isinstance(s,SelectStmt):
            node=PlanNode("SeqScan",{"table":s.table})
            if s.where:node=PlanNode("Filter",{"predicate":s.where,"display":expr_text(s.where)},[node])
            if s.order_by:node=PlanNode("Sort",{"keys":[(item.column,item.direction) for item in s.order_by]},[node])
            if s.columns!=["*"]:node=PlanNode("Project",{"columns":s.columns},[node])
            return node
        raise TypeError(type(s).__name__)
