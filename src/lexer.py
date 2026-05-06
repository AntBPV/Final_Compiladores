# ─────────────────────────────────────────────────────────────────────────────
#  lexer.py  –  Analizador Léxico para "Guiones Interactivos"
#  Simula el comportamiento del lexer generado por ANTLR4
# ─────────────────────────────────────────────────────────────────────────────
import re
from dataclasses import dataclass
from typing import List


# ── Tipos de tokens ──────────────────────────────────────────────────────────
class TokenType:
    # Palabras clave
    ESCENA   = 'ESCENA'
    DECIR    = 'DECIR'
    OPCION   = 'OPCION'
    IR_A     = 'IR_A'
    VAR      = 'VAR'
    SI       = 'SI'
    SINO     = 'SINO'
    VERDADERO = 'VERDADERO'
    FALSO    = 'FALSO'

    # Literales
    STRING   = 'STRING'
    NUMBER   = 'NUMBER'
    BOOL     = 'BOOL'
    ID       = 'ID'

    # Operadores
    EQUAL    = 'EQUAL'      # ==
    NEQ      = 'NEQ'        # !=
    LTE      = 'LTE'        # <=
    GTE      = 'GTE'        # >=
    LT       = 'LT'         # <
    GT       = 'GT'         # >
    ASSIGN   = 'ASSIGN'     # =
    PLUS     = 'PLUS'       # +

    # Delimitadores
    LBRACE   = 'LBRACE'     # {
    RBRACE   = 'RBRACE'     # }
    LPAREN   = 'LPAREN'     # (
    RPAREN   = 'RPAREN'     # )
    SEMI     = 'SEMI'       # ;

    # Especiales
    EOF      = 'EOF'
    UNKNOWN  = 'UNKNOWN'


@dataclass
class Token:
    type:   str
    value:  str
    line:   int
    column: int

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, L{self.line}:C{self.column})"


# ── Error léxico ──────────────────────────────────────────────────────────────
class LexerError(Exception):
    def __init__(self, msg: str, line: int, column: int):
        super().__init__(msg)
        self.line   = line
        self.column = column


# ── Lexer ─────────────────────────────────────────────────────────────────────
class Lexer:
    KEYWORDS = {
        'escena':     TokenType.ESCENA,
        'decir':      TokenType.DECIR,
        'opcion':     TokenType.OPCION,
        'ir_a':       TokenType.IR_A,
        'var':        TokenType.VAR,
        'si':         TokenType.SI,
        'sino':       TokenType.SINO,
        'verdadero':  TokenType.BOOL,
        'falso':      TokenType.BOOL,
    }

    # Patrones ordenados: los más específicos primero
    TOKEN_SPEC = [
        ('COMMENT', r'//[^\r\n]*'),
        ('STRING',  r'"[^"\r\n]*"'),
        ('NUMBER',  r'\d+(?:\.\d+)?'),
        ('EQUAL',   r'=='),
        ('NEQ',     r'!='),
        ('LTE',     r'<='),
        ('GTE',     r'>='),
        ('LT',      r'<'),
        ('GT',      r'>'),
        ('ASSIGN',  r'='),
        ('PLUS',    r'\+'),
        ('LBRACE',  r'\{'),
        ('RBRACE',  r'\}'),
        ('LPAREN',  r'\('),
        ('RPAREN',  r'\)'),
        ('SEMI',    r';'),
        ('WS',      r'[ \t\r\n]+'),
        ('ID',      r'[a-zA-Z_\u00e0-\u024f][a-zA-Z0-9_\u00e0-\u024f]*'),
        ('UNKNOWN', r'.'),
    ]

    MASTER_RE = re.compile(
        '|'.join(f'(?P<{name}>{pat})' for name, pat in TOKEN_SPEC),
        re.UNICODE
    )

    def __init__(self, source: str):
        self.source = source
        self.tokens: List[Token] = []
        self.errors: List[LexerError] = []

    def tokenize(self) -> List[Token]:
        line   = 1
        col    = 1
        line_start = 0

        for mo in self.MASTER_RE.finditer(self.source):
            kind  = mo.lastgroup
            value = mo.group()
            col   = mo.start() - line_start + 1

            if kind == 'WS':
                newlines = value.count('\n')
                if newlines:
                    line      += newlines
                    line_start = mo.end() - (len(value) - value.rfind('\n') - 1)
                continue

            if kind == 'COMMENT':
                continue

            if kind == 'UNKNOWN':
                err = LexerError(
                    f"Carácter desconocido '{value}'", line, col
                )
                self.errors.append(err)
                continue

            if kind == 'ID':
                kind = self.KEYWORDS.get(value, TokenType.ID)

            self.tokens.append(Token(kind, value, line, col))

        self.tokens.append(Token(TokenType.EOF, '', line, col))
        return self.tokens

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def print_errors(self):
        for e in self.errors:
            print(f"  [ERROR LÉXICO] Línea {e.line}, Col {e.column}: {e}")
