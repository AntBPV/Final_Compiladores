# ─────────────────────────────────────────────────────────────────────────────
#  semantic.py  –  Analizador Semántico + Tabla de Símbolos
# ─────────────────────────────────────────────────────────────────────────────
from typing import Dict, List, Set, Optional, Any
from ast_nodes import (
    Program, Scene,
    DecirStmt, OpcionStmt, AsignarStmt, SiStmt,
    Condition,
    StringLiteral, NumberLiteral, BoolLiteral, VarExpr, ConcatExpr,
)


# ── Entrada de la tabla de símbolos ──────────────────────────────────────────

class SymbolEntry:
    def __init__(self, name: str, sym_type: str, scope: str, line: int, col: int):
        self.name     = name
        self.sym_type = sym_type   # 'escena' | 'variable'
        self.scope    = scope      # nombre de la escena donde vive
        self.line     = line
        self.col      = col

    def __repr__(self):
        return (f"SymbolEntry(name={self.name!r}, type={self.sym_type!r}, "
                f"scope={self.scope!r}, L{self.line}:C{self.col})")


# ── Tabla de símbolos ────────────────────────────────────────────────────────

class SymbolTable:
    def __init__(self):
        # tabla global: escenas
        self._global: Dict[str, SymbolEntry] = {}
        # tabla local por escena: variables
        self._local:  Dict[str, Dict[str, SymbolEntry]] = {}

    def add_scene(self, name: str, line: int, col: int):
        self._global[name] = SymbolEntry(name, 'escena', 'global', line, col)
        self._local[name]  = {}

    def scene_exists(self, name: str) -> bool:
        return name in self._global

    def add_var(self, scope: str, name: str, line: int, col: int):
        if scope not in self._local:
            self._local[scope] = {}
        self._local[scope][name] = SymbolEntry(name, 'variable', scope, line, col)

    def var_exists(self, scope: str, name: str) -> bool:
        return scope in self._local and name in self._local[scope]

    def get_var(self, scope: str, name: str) -> Optional[SymbolEntry]:
        return self._local.get(scope, {}).get(name)

    def dump(self) -> str:
        lines = []
        lines.append("╔══════════════════════════════════════════════════════╗")
        lines.append("║              TABLA DE SÍMBOLOS                       ║")
        lines.append("╠══════════╦════════════╦══════════════╦══════════════╣")
        lines.append("║ Nombre   ║ Tipo       ║ Ámbito       ║ Posición     ║")
        lines.append("╠══════════╬════════════╬══════════════╬══════════════╣")

        for entry in self._global.values():
            lines.append(
                f"║ {entry.name:<8} ║ {entry.sym_type:<10} ║ {'global':<12} ║ "
                f"L{entry.line}:C{entry.col:<9} ║"
            )

        for scope, vars_ in self._local.items():
            for entry in vars_.values():
                lines.append(
                    f"║ {entry.name:<8} ║ {entry.sym_type:<10} ║ {scope:<12} ║ "
                    f"L{entry.line}:C{entry.col:<9} ║"
                )

        lines.append("╚══════════╩════════════╩══════════════╩══════════════╝")
        return '\n'.join(lines)


# ── Error semántico ──────────────────────────────────────────────────────────

class SemanticError(Exception):
    def __init__(self, msg: str, line: int, col: int):
        super().__init__(msg)
        self.line = line
        self.col  = col


# ── Analizador semántico ─────────────────────────────────────────────────────

class SemanticAnalyzer:
    def __init__(self):
        self.table  = SymbolTable()
        self.errors: List[SemanticError] = []
        self._current_scope: str = ''

    # ── Entrada principal ────────────────────────────────────────────────────

    def analyze(self, program: Program):
        # Paso 1: registrar todas las escenas (permite referencias hacia adelante)
        for scene in program.scenes:
            if self.table.scene_exists(scene.name):
                self._error(
                    f"La escena '{scene.name}' ya fue declarada",
                    scene.line, scene.col
                )
            else:
                self.table.add_scene(scene.name, scene.line, scene.col)

        # Paso 2: análisis de cada escena
        for scene in program.scenes:
            self._analyze_scene(scene)

    def _analyze_scene(self, scene: Scene):
        self._current_scope = scene.name
        for stmt in scene.statements:
            self._analyze_stmt(stmt)

    # ── Sentencias ────────────────────────────────────────────────────────────

    def _analyze_stmt(self, stmt):
        if isinstance(stmt, DecirStmt):
            self._analyze_expr(stmt.expr)

        elif isinstance(stmt, OpcionStmt):
            if not self.table.scene_exists(stmt.target):
                self._error(
                    f"La opción apunta a la escena '{stmt.target}', "
                    f"pero esta escena no está definida en el programa",
                    stmt.line, stmt.col
                )

        elif isinstance(stmt, AsignarStmt):
            self._analyze_expr(stmt.expr)
            if stmt.is_decl:
                if self.table.var_exists(self._current_scope, stmt.name):
                    self._error(
                        f"La variable '{stmt.name}' ya fue declarada en "
                        f"la escena '{self._current_scope}'",
                        stmt.line, stmt.col
                    )
                else:
                    self.table.add_var(
                        self._current_scope, stmt.name,
                        stmt.line, stmt.col
                    )
            else:
                if not self.table.var_exists(self._current_scope, stmt.name):
                    self._error(
                        f"Variable '{stmt.name}' no declarada en la escena "
                        f"'{self._current_scope}'. Usa 'var {stmt.name} = ...'",
                        stmt.line, stmt.col
                    )

        elif isinstance(stmt, SiStmt):
            self._analyze_condition(stmt.condition)
            for s in stmt.then_body:
                self._analyze_stmt(s)
            if stmt.else_body:
                for s in stmt.else_body:
                    self._analyze_stmt(s)

    # ── Condición ──────────────────────────────────────────────────────────────

    def _analyze_condition(self, cond: Condition):
        self._analyze_expr(cond.left)
        self._analyze_expr(cond.right)

    # ── Expresiones ──────────────────────────────────────────────────────────

    def _analyze_expr(self, expr):
        if isinstance(expr, VarExpr):
            if not self.table.var_exists(self._current_scope, expr.name):
                self._error(
                    f"Variable '{expr.name}' no declarada en la escena "
                    f"'{self._current_scope}'",
                    expr.line, expr.col
                )
        elif isinstance(expr, ConcatExpr):
            self._analyze_expr(expr.left)
            self._analyze_expr(expr.right)
        # StringLiteral, NumberLiteral, BoolLiteral: siempre válidos

    # ── Utilidades ────────────────────────────────────────────────────────────

    def _error(self, msg: str, line: int, col: int):
        self.errors.append(SemanticError(msg, line, col))

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def print_errors(self):
        for e in self.errors:
            print(f"  [ERROR SEMÁNTICO] Línea {e.line}, Col {e.col}: {e}")
