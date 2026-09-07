from dataclasses import dataclass
from enum import Enum, auto
from .errors import SourceLocation


class TokenType(Enum):
    KEYWORD = auto(); IDENTIFIER = auto(); INTEGER = auto(); FLOAT = auto()
    STRING = auto(); OPERATOR = auto(); DELIMITER = auto(); EOF = auto()


@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str
    location: SourceLocation
    value: object = None

    def to_dict(self):
        return {"type": self.type.name, "lexeme": self.lexeme,
                "line": self.location.line, "column": self.location.column, "value": self.value}


KEYWORDS = {"CREATE","TABLE","INSERT","INTO","VALUES","SELECT","FROM","WHERE","DELETE",
            "UPDATE","SET","ORDER","BY","ASC","DESC",
            "INT","VARCHAR","AND","OR","NOT","TRUE","FALSE","NULL","EXPLAIN"}
