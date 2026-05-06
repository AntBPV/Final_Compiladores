# ─────────────────────────────────────────────────────────────────────────────
#  parser.py  –  Analizador Sintáctico (Descenso Recursivo)
#  Consume la lista de tokens del Lexer y construye el AST
# ─────────────────────────────────────────────────────────────────────────────
from typing import List, Optional
from lexer import Token, TokenType
from ast_nodes import (
    Program, Scene,
    DecirStmt, OpcionStmt, AsignarStmt, SiStmt,
    Condition,
    StringLiteral, NumberLiteral, BoolLiteral, VarExpr, ConcatExpr,
)


class ParseError(Exception):
    def __init__(self, msg: str, line: int, col: int):
        super().__init__(msg)
        self.line = line
        self.col  = col


class Parser:
    COMPARISON_OPS = {
        TokenType.EQUAL, TokenType.NEQ,
        TokenType.LT, TokenType.GT,
        TokenType.LTE, TokenType.GTE,
    }

    def __init__(self, tokens: List[Token]):
        self.tokens  = tokens
        self.pos     = 0
        self.errors: List[ParseError] = []

    # ── Utilidades ──────────────────────────────────────────────────────────

    def current(self) -> Token:
        return self.tokens[self.pos]

    def peek(self, offset: int = 1) -> Token:
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else self.tokens[-1]

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def check(self, *types: str) -> bool:
        return self.current().type in types

    def match(self, *types: str) -> Optional[Token]:
        if self.check(*types):
            return self.advance()
        return None

    def expect(self, ttype: str, msg: str = '') -> Token:
        if self.check(ttype):
            return self.advance()
        tok = self.current()
        err_msg = msg or f"Se esperaba '{ttype}' pero se encontró '{tok.value}'"
        raise ParseError(err_msg, tok.line, tok.column)

    def synchronize(self, *stop_types: str):
        """Recuperación de errores: avanza hasta encontrar un token de sincronía."""
        while not self.check(TokenType.EOF, *stop_types):
            self.advance()

    # ── Reglas gramaticales ─────────────────────────────────────────────────

    def parse(self) -> Program:
        scenes = []
        while not self.check(TokenType.EOF):
            try:
                scenes.append(self.parse_scene())
            except ParseError as e:
                self.errors.append(e)
                self.synchronize(TokenType.ESCENA)
        return Program(scenes=scenes)

    def parse_scene(self) -> Scene:
        tok = self.expect(TokenType.ESCENA, "Se esperaba la palabra clave 'escena'")
        name_tok = self.expect(TokenType.ID, "Se esperaba un nombre de escena (identificador)")
        self.expect(TokenType.LBRACE, f"Se esperaba '{{' después del nombre de escena '{name_tok.value}'")

        stmts = []
        if self.check(TokenType.RBRACE):
            raise ParseError(
                f"La escena '{name_tok.value}' está vacía; debe tener al menos una sentencia",
                name_tok.line, name_tok.column
            )

        while not self.check(TokenType.RBRACE, TokenType.EOF, TokenType.ESCENA):
            prev_pos = self.pos
            try:
                stmts.append(self.parse_statement())
            except ParseError as e:
                self.errors.append(e)
                self.synchronize(TokenType.RBRACE, TokenType.DECIR,
                                  TokenType.OPCION, TokenType.VAR,
                                  TokenType.SI, TokenType.ID,
                                  TokenType.ESCENA)
            if self.pos == prev_pos:
                self.advance()

        self.expect(TokenType.RBRACE, "Se esperaba '}' para cerrar la escena")
        scene = Scene(name=name_tok.value, statements=stmts)
        scene.line = tok.line
        scene.col  = tok.column
        return scene

    def parse_statement(self):
        tok = self.current()

        if self.check(TokenType.DECIR):
            return self.parse_decir()
        if self.check(TokenType.OPCION):
            return self.parse_opcion()
        if self.check(TokenType.VAR):
            return self.parse_asignar(is_decl=True)
        if self.check(TokenType.SI):
            return self.parse_si()
        if self.check(TokenType.ID) and self.peek().type == TokenType.ASSIGN:
            return self.parse_asignar(is_decl=False)

        raise ParseError(
            f"Sentencia no reconocida: '{tok.value}'. "
            f"Se esperaba 'decir', 'opcion', 'var', 'si' o un identificador",
            tok.line, tok.column
        )

    def parse_decir(self) -> DecirStmt:
        tok = self.advance()   # consume 'decir'
        expr = self.parse_expr()
        self.expect(TokenType.SEMI, "Se esperaba ';' al final de 'decir'")
        s = DecirStmt(expr=expr)
        s.line, s.col = tok.line, tok.column
        return s

    def parse_opcion(self) -> OpcionStmt:
        tok = self.advance()   # consume 'opcion'
        label_tok = self.expect(TokenType.STRING, "Se esperaba texto (STRING) en 'opcion'")
        self.expect(TokenType.IR_A, "Se esperaba 'ir_a' después del texto de opción")
        target_tok = self.expect(TokenType.ID, "Se esperaba nombre de escena después de 'ir_a'")
        self.expect(TokenType.SEMI, "Se esperaba ';' al final de 'opcion'")
        s = OpcionStmt(
            label=label_tok.value.strip('"'),
            target=target_tok.value
        )
        s.line, s.col = tok.line, tok.column
        return s

    def parse_asignar(self, is_decl: bool) -> AsignarStmt:
        tok = self.current()
        if is_decl:
            self.advance()  # consume 'var'
        name_tok = self.expect(TokenType.ID, "Se esperaba un nombre de variable")
        self.expect(TokenType.ASSIGN, "Se esperaba '=' en la asignación")
        expr = self.parse_expr()
        self.expect(TokenType.SEMI, "Se esperaba ';' al final de la asignación")
        s = AsignarStmt(name=name_tok.value, expr=expr, is_decl=is_decl)
        s.line, s.col = tok.line, tok.column
        return s

    def parse_si(self) -> SiStmt:
        tok = self.advance()   # consume 'si'
        self.expect(TokenType.LPAREN, "Se esperaba '(' después de 'si'")
        cond = self.parse_condition()
        self.expect(TokenType.RPAREN, "Se esperaba ')' para cerrar la condición")
        self.expect(TokenType.LBRACE, "Se esperaba '{' para abrir el bloque 'si'")

        then_body = []
        while not self.check(TokenType.RBRACE, TokenType.EOF):
            then_body.append(self.parse_statement())
        self.expect(TokenType.RBRACE, "Se esperaba '}' para cerrar el bloque 'si'")

        else_body = None
        if self.match(TokenType.SINO):
            self.expect(TokenType.LBRACE, "Se esperaba '{' para abrir el bloque 'sino'")
            else_body = []
            while not self.check(TokenType.RBRACE, TokenType.EOF):
                else_body.append(self.parse_statement())
            self.expect(TokenType.RBRACE, "Se esperaba '}' para cerrar el bloque 'sino'")

        s = SiStmt(condition=cond, then_body=then_body, else_body=else_body)
        s.line, s.col = tok.line, tok.column
        return s

    def parse_condition(self) -> Condition:
        left = self.parse_expr()
        op_tok = self.current()
        if op_tok.type not in self.COMPARISON_OPS:
            raise ParseError(
                f"Operador de comparación inválido: '{op_tok.value}'. "
                f"Use ==, !=, <, >, <=, >=",
                op_tok.line, op_tok.column
            )
        self.advance()
        right = self.parse_expr()
        c = Condition(left=left, op=op_tok.value, right=right)
        c.line, c.col = op_tok.line, op_tok.column
        return c

    def parse_expr(self):
        left = self.parse_primary()
        while self.check(TokenType.PLUS):
            self.advance()
            right = self.parse_primary()
            node = ConcatExpr(left=left, right=right)
            node.line = left.line
            left = node
        return left

    def parse_primary(self):
        tok = self.current()

        if self.check(TokenType.STRING):
            self.advance()
            n = StringLiteral(value=tok.value.strip('"'))
            n.line, n.col = tok.line, tok.column
            return n

        if self.check(TokenType.NUMBER):
            self.advance()
            n = NumberLiteral(value=float(tok.value))
            n.line, n.col = tok.line, tok.column
            return n

        if self.check(TokenType.BOOL):
            self.advance()
            n = BoolLiteral(value=(tok.value == 'verdadero'))
            n.line, n.col = tok.line, tok.column
            return n

        if self.check(TokenType.ID):
            self.advance()
            n = VarExpr(name=tok.value)
            n.line, n.col = tok.line, tok.column
            return n

        raise ParseError(
            f"Expresión no válida: se encontró '{tok.value}'. "
            f"Se esperaba un texto, número, booleano o variable",
            tok.line, tok.column
        )

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def print_errors(self):
        for e in self.errors:
            print(f"  [ERROR SINTÁCTICO] Línea {e.line}, Col {e.col}: {e}")
