from dataclasses import dataclass, field, asdict
from .errors import SourceLocation


@dataclass
class Node:
    location: SourceLocation
    def to_dict(self):
        d = asdict(self); d["node"] = type(self).__name__; return d

@dataclass
class Expr(Node): inferred_type: str | None = field(default=None, init=False)
@dataclass
class IdentifierExpr(Expr): name: str = ""
@dataclass
class LiteralExpr(Expr): value: object = None; literal_type: str = "NULL"
@dataclass
class UnaryExpr(Expr): operator: str = ""; operand: Expr | None = None
@dataclass
class BinaryExpr(Expr): left: Expr | None = None; operator: str = ""; right: Expr | None = None

@dataclass
class ColumnDef(Node): name: str = ""; data_type: str = ""; length: int | None = None
@dataclass
class Statement(Node): pass
@dataclass
class CreateTableStmt(Statement): table: str = ""; columns: list[ColumnDef] = field(default_factory=list)
@dataclass
class InsertStmt(Statement): table: str = ""; columns: list[str] = field(default_factory=list); values: list[Expr] = field(default_factory=list)
@dataclass
class OrderItem(Node): column: str = ""; direction: str = "ASC"
@dataclass
class SelectStmt(Statement):
    table: str = ""; columns: list[str] = field(default_factory=list); where: Expr | None = None
    order_by: list[OrderItem] = field(default_factory=list)
@dataclass
class DeleteStmt(Statement): table: str = ""; where: Expr | None = None
@dataclass
class UpdateStmt(Statement):
    table: str = ""; assignments: list[tuple[str, Expr]] = field(default_factory=list); where: Expr | None = None
