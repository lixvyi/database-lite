from dataclasses import dataclass


@dataclass
class SourceLocation:
    line: int
    column: int
    offset: int = 0


class MiniDBError(Exception):
    stage = "Database"

    def __init__(self, message: str, location: SourceLocation | None = None, expected=None):
        self.message = message
        self.location = location
        self.expected = expected or []
        where = f" at line {location.line}, column {location.column}" if location else ""
        hint = f"; expected: {' | '.join(self.expected)}" if self.expected else ""
        super().__init__(f"{self.stage}Error{where}: {message}{hint}")


class LexicalError(MiniDBError): stage = "Lexical"
class SyntaxError(MiniDBError): stage = "Syntax"
class SemanticError(MiniDBError): stage = "Semantic"
class StorageError(MiniDBError): stage = "Storage"
class PermissionDenied(MiniDBError): stage = "Permission"
