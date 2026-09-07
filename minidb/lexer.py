from .errors import LexicalError, SourceLocation
from .tokens import KEYWORDS, Token, TokenType


class Lexer:
    def __init__(self, source: str):
        self.source, self.i, self.line, self.col = source, 0, 1, 1

    def here(self): return SourceLocation(self.line, self.col, self.i)
    def peek(self, n=0):
        j = self.i + n
        return self.source[j] if j < len(self.source) else "\0"
    def advance(self):
        ch = self.peek(); self.i += 1
        if ch == "\n": self.line, self.col = self.line + 1, 1
        else: self.col += 1
        return ch

    def tokenize(self):
        out = []
        while self.i < len(self.source):
            ch = self.peek()
            if ch.isspace(): self.advance(); continue
            if ch == "-" and self.peek(1) == "-":
                while self.peek() not in ("\n", "\0"): self.advance()
                continue
            if ch == "/" and self.peek(1) == "*":
                start = self.here(); self.advance(); self.advance()
                while not (self.peek() == "*" and self.peek(1) == "/"):
                    if self.peek() == "\0": raise LexicalError("unterminated block comment", start)
                    self.advance()
                self.advance(); self.advance(); continue
            start = self.here()
            if ch.isalpha() or ch == "_":
                text = self.advance()
                while self.peek().isalnum() or self.peek() == "_": text += self.advance()
                upper = text.upper()
                out.append(Token(TokenType.KEYWORD if upper in KEYWORDS else TokenType.IDENTIFIER,
                                 upper if upper in KEYWORDS else text, start, upper if upper in KEYWORDS else text))
            elif ch.isdigit():
                text = self.advance()
                while self.peek().isdigit(): text += self.advance()
                kind, value = TokenType.INTEGER, int(text)
                if self.peek() == ".":
                    text += self.advance()
                    if not self.peek().isdigit(): raise LexicalError("digit expected after decimal point", self.here())
                    while self.peek().isdigit(): text += self.advance()
                    kind, value = TokenType.FLOAT, float(text)
                if self.peek().isalpha() or self.peek() == "_": raise LexicalError("invalid numeric literal", start)
                out.append(Token(kind, text, start, value))
            elif ch == "'":
                self.advance(); value = ""; raw = "'"
                while True:
                    if self.peek() in ("\0", "\n"): raise LexicalError("unterminated string literal", start)
                    if self.peek() == "'":
                        raw += self.advance()
                        if self.peek() == "'": raw += self.advance(); value += "'"; continue
                        break
                    c = self.advance(); raw += c; value += c
                out.append(Token(TokenType.STRING, raw, start, value))
            elif ch in "(),;": out.append(Token(TokenType.DELIMITER, self.advance(), start, ch))
            elif ch in "=<>!+-*/":
                text = self.advance()
                if self.peek() == "=" and text in "=<>!": text += self.advance()
                if text == "!": raise LexicalError("'!' must be followed by '='", start)
                out.append(Token(TokenType.OPERATOR, text, start, text))
            else: raise LexicalError(f"illegal character {ch!r}", start)
        out.append(Token(TokenType.EOF, "<EOF>", self.here()))
        return out
