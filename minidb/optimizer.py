from copy import deepcopy
from .ast import BinaryExpr,LiteralExpr,UnaryExpr
from .plan import PlanNode,expr_text
from .errors import SemanticError


def eval_const(op,a,b):
    return {"+":lambda:a+b,"-":lambda:a-b,"*":lambda:a*b,"/":lambda:a/b,
            "=":lambda:a==b,"==":lambda:a==b,"!=":lambda:a!=b,">":lambda:a>b,">=":lambda:a>=b,"<":lambda:a<b,"<=":lambda:a<=b,
            "AND":lambda:bool(a and b),"OR":lambda:bool(a or b)}[op]()


def fold(e):
    if isinstance(e,BinaryExpr):
        e.left,e.right=fold(e.left),fold(e.right)
        if isinstance(e.left,LiteralExpr) and isinstance(e.right,LiteralExpr):
            try:value=eval_const(e.operator,e.left.value,e.right.value)
            except ZeroDivisionError:raise SemanticError("division by zero in constant expression",e.location)
            return LiteralExpr(e.location,value,"BOOL" if isinstance(value,bool) else "FLOAT" if isinstance(value,float) else "INT")
        if e.operator=="AND":
            if isinstance(e.left,LiteralExpr) and e.left.value is True:return e.right
            if isinstance(e.right,LiteralExpr) and e.right.value is True:return e.left
        if e.operator=="OR":
            if isinstance(e.left,LiteralExpr) and e.left.value is False:return e.right
            if isinstance(e.right,LiteralExpr) and e.right.value is False:return e.left
    if isinstance(e,UnaryExpr):
        e.operand=fold(e.operand)
        if isinstance(e.operand,LiteralExpr):return LiteralExpr(e.location,not e.operand.value,"BOOL")
    return e


class Optimizer:
    """规则：常量折叠、布尔化简、恒真 Filter 消除、Project[*] 在建计划阶段消除。"""
    def optimize(self,plan):
        out=deepcopy(plan)
        def visit(n):
            n.children=[visit(c) for c in n.children]
            if n.kind=="Filter":
                n.args["predicate"]=fold(n.args["predicate"]); n.args["display"]=expr_text(n.args["predicate"])
                if isinstance(n.args["predicate"],LiteralExpr) and n.args["predicate"].value is True:return n.children[0]
            return n
        return visit(out)
