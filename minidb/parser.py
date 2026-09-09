from .ast import *
from .errors import SyntaxError
from .lexer import Lexer
from .tokens import TokenType


class Parser:
    def __init__(self, source: str): self.tokens, self.i = Lexer(source).tokenize(), 0
    @property
    def current(self): return self.tokens[self.i]
    def match(self, *lexemes):
        if self.current.lexeme.upper() in lexemes: self.i += 1; return True
        return False
    def expect(self, lexeme):
        if not self.match(lexeme): raise SyntaxError(f"unexpected token {self.current.lexeme!r}", self.current.location, [lexeme])
        return self.tokens[self.i-1]
    def identifier(self):
        t = self.current
        if t.type != TokenType.IDENTIFIER: raise SyntaxError(f"unexpected token {t.lexeme!r}", t.location, ["IDENTIFIER"])
        self.i += 1; return t
    def parse_all(self):
        stmts = []
        while self.current.type != TokenType.EOF: stmts.append(self.statement())
        return stmts
    def statement(self):
        if self.match("CREATE"): stmt = self.create()
        elif self.match("INSERT"): stmt = self.insert()
        elif self.match("SELECT"): stmt = self.select()
        elif self.match("DELETE"): stmt = self.delete()
        elif self.match("UPDATE"): stmt = self.update()
        else: raise SyntaxError(f"unexpected token {self.current.lexeme!r}", self.current.location, ["CREATE","INSERT","SELECT","DELETE","UPDATE"])
        self.expect(";"); return stmt
    def create(self):
        loc=self.tokens[self.i-1].location; self.expect("TABLE"); table=self.identifier().lexeme; self.expect("("); cols=[]
        while True:
            name=self.identifier(); typ=self.current
            if not self.match("INT","VARCHAR"): raise SyntaxError("column type expected",typ.location,["INT","VARCHAR"])
            length=None
            if typ.lexeme=="VARCHAR" and self.match("("):
                if self.current.type!=TokenType.INTEGER: raise SyntaxError("VARCHAR length must be integer",self.current.location,["INTEGER"])
                length=self.current.value; self.i+=1; self.expect(")")
            cols.append(ColumnDef(name.location,name.lexeme,typ.lexeme,length))
            if not self.match(","): break
        self.expect(")"); return CreateTableStmt(loc,table,cols)
    def insert(self):
        loc=self.tokens[self.i-1].location; self.expect("INTO"); table=self.identifier().lexeme; self.expect("("); cols=[]
        while True:
            cols.append(self.identifier().lexeme)
            if not self.match(","): break
        self.expect(")"); self.expect("VALUES"); self.expect("("); vals=[]
        while True:
            vals.append(self.primary())
            if not self.match(","): break
        self.expect(")"); return InsertStmt(loc,table,cols,vals)
    def select(self):
        loc=self.tokens[self.i-1].location; cols=[]
        if self.match("*"): cols=["*"]
        else:
            while True:
                cols.append(self.identifier().lexeme)
                if not self.match(","): break
        self.expect("FROM"); table=self.identifier().lexeme; where=self.expression() if self.match("WHERE") else None;order=[]
        if self.match("ORDER"):
            self.expect("BY")
            while True:
                column=self.identifier();direction="ASC"
                if self.match("ASC"):direction="ASC"
                elif self.match("DESC"):direction="DESC"
                order.append(OrderItem(column.location,column.lexeme,direction))
                if not self.match(","):break
        return SelectStmt(loc,table,cols,where,order)
    def delete(self):
        loc=self.tokens[self.i-1].location; self.expect("FROM"); table=self.identifier().lexeme
        return DeleteStmt(loc,table,self.expression() if self.match("WHERE") else None)
    def update(self):
        loc=self.tokens[self.i-1].location;table=self.identifier().lexeme;self.expect("SET");assignments=[]
        while True:
            column=self.identifier();self.expect("=");assignments.append((column.lexeme,self.expression()))
            if not self.match(","):break
        where=self.expression() if self.match("WHERE") else None
        return UpdateStmt(loc,table,assignments,where)
    def expression(self): return self.or_expr()
    def or_expr(self):
        expr=self.and_expr()
        while self.match("OR"): expr=BinaryExpr(expr.location,expr,"OR",self.and_expr())
        return expr
    def and_expr(self):
        expr=self.not_expr()
        while self.match("AND"): expr=BinaryExpr(expr.location,expr,"AND",self.not_expr())
        return expr
    def not_expr(self):
        if self.match("NOT"):
            t=self.tokens[self.i-1]; return UnaryExpr(t.location,"NOT",self.not_expr())
        return self.comparison()
    def comparison(self):
        expr=self.additive()
        if self.current.lexeme in ("=","==","!=",">",">=","<","<="):
            op=self.current.lexeme; self.i+=1; expr=BinaryExpr(expr.location,expr,op,self.additive())
        return expr
    def additive(self):
        expr=self.multiplicative()
        while self.current.lexeme in ("+","-"):
            op=self.current.lexeme; self.i+=1; expr=BinaryExpr(expr.location,expr,op,self.multiplicative())
        return expr
    def multiplicative(self):
        expr=self.primary()
        while self.current.lexeme in ("*","/"):
            op=self.current.lexeme; self.i+=1; expr=BinaryExpr(expr.location,expr,op,self.primary())
        return expr
    def primary(self):
        t=self.current
        if t.type==TokenType.IDENTIFIER: self.i+=1; return IdentifierExpr(t.location,t.lexeme)
        if t.type in (TokenType.INTEGER,TokenType.FLOAT,TokenType.STRING):
            self.i+=1; return LiteralExpr(t.location,t.value,{TokenType.INTEGER:"INT",TokenType.FLOAT:"FLOAT",TokenType.STRING:"VARCHAR"}[t.type])
        if self.match("("):
            expr=self.expression(); self.expect(")"); return expr
        raise SyntaxError(f"unexpected token {t.lexeme!r}",t.location,["IDENTIFIER","CONST","(","NOT"])
