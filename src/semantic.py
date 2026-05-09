# ─────────────────────────────────────────────────────────────────────────────
#  semantic.py  –  Analizador Semántico + Tabla de Símbolos
# ─────────────────────────────────────────────────────────────────────────────
from typing import Dict, List, Optional
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
        self.sym_type = sym_type
        self.scope    = scope
        self.line     = line
        self.col      = col

    def __repr__(self):
        return (f"SymbolEntry(name={self.name!r}, type={self.sym_type!r}, "
                f"scope={self.scope!r}, L{self.line}:C{self.col})")


# ── Tabla de símbolos ────────────────────────────────────────────────────────

class SymbolTable:
    def __init__(self):
        self._global: Dict[str, SymbolEntry] = {}
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


# ── Registro de verificaciones ────────────────────────────────────────────────

class CheckLog:
    """Registra cada verificación semántica realizada (OK o ERROR)."""

    def __init__(self):
        self._entries: List[dict] = []

    def ok(self, rule: str, detail: str, scope: str, line: int):
        self._entries.append(
            {'status': 'OK', 'rule': rule, 'detail': detail,
             'scope': scope, 'line': line}
        )

    def fail(self, rule: str, detail: str, scope: str, line: int):
        self._entries.append(
            {'status': 'ERROR', 'rule': rule, 'detail': detail,
             'scope': scope, 'line': line}
        )

    def dump(self) -> str:
        if not self._entries:
            return "  (sin verificaciones registradas)"

        rw = max(len(e['rule'])   for e in self._entries) + 2
        dw = max(len(e['detail']) for e in self._entries) + 2
        sw = max(len(e['scope'])  for e in self._entries) + 2
        rw = max(rw, 16); dw = max(dw, 20); sw = max(sw, 10)

        top = f"  ┌──────┬{'─'*rw}┬{'─'*dw}┬{'─'*sw}┬────────┐"
        hdr = f"  │ {'ST':<4} │ {'REGLA':<{rw-2}} │ {'DETALLE':<{dw-2}} │ {'ÁMBITO':<{sw-2}} │ {'LÍNEA':<6} │"
        mid = f"  ╞══════╪{'═'*rw}╪{'═'*dw}╪{'═'*sw}╪════════╡"
        sep = f"  ├──────┼{'─'*rw}┼{'─'*dw}┼{'─'*sw}┼────────┤"
        bot = f"  └──────┴{'─'*rw}┴{'─'*dw}┴{'─'*sw}┴────────┘"

        lines = [top, hdr, mid]
        for i, e in enumerate(self._entries):
            st   = ' ✓ ' if e['status'] == 'OK' else ' ✗ '
            row  = (f"  │{st:<6}│ {e['rule']:<{rw-2}} │ {e['detail']:<{dw-2}} │"
                    f" {e['scope']:<{sw-2}} │ {e['line']:<6} │")
            lines.append(row)
            if i < len(self._entries) - 1:
                lines.append(sep)
        lines.append(bot)

        ok_count  = sum(1 for e in self._entries if e['status'] == 'OK')
        err_count = sum(1 for e in self._entries if e['status'] == 'ERROR')
        lines.append(f"  Verificaciones: {len(self._entries)} total  |"
                     f"  ✓ {ok_count} correctas  |  ✗ {err_count} con error\n")
        return '\n'.join(lines)


# ── Error semántico ───────────────────────────────────────────────────────────

class SemanticError(Exception):
    def __init__(self, msg: str, line: int, col: int):
        super().__init__(msg)
        self.line = line
        self.col  = col


# ── Analizador semántico ──────────────────────────────────────────────────────

class SemanticAnalyzer:
    def __init__(self):
        self.table          = SymbolTable()
        self.log            = CheckLog()
        self.errors: List[SemanticError] = []
        self._current_scope: str = ''

    # ── Entrada principal ─────────────────────────────────────────────────────

    def analyze(self, program: Program):
        # Paso 1: registrar todas las escenas
        for scene in program.scenes:
            if self.table.scene_exists(scene.name):
                self._error(
                    f"La escena '{scene.name}' ya fue declarada",
                    scene.line, scene.col
                )
                self.log.fail(
                    'Escena única',
                    f"escena '{scene.name}' duplicada",
                    'global', scene.line
                )
            else:
                self.table.add_scene(scene.name, scene.line, scene.col)
                self.log.ok(
                    'Declaración escena',
                    f"escena '{scene.name}' registrada",
                    'global', scene.line
                )

        # Paso 2: analizar contenido de cada escena
        for scene in program.scenes:
            self._analyze_scene(scene)

    def _analyze_scene(self, scene: Scene):
        self._current_scope = scene.name
        for stmt in scene.statements:
            self._analyze_stmt(stmt)

    # ── Sentencias ────────────────────────────────────────────────────────────

    def _analyze_stmt(self, stmt):
        sc = self._current_scope

        if isinstance(stmt, DecirStmt):
            self._analyze_expr(stmt.expr)
            self.log.ok(
                'Sentencia decir',
                f"expresión válida en 'decir'",
                sc, stmt.line
            )

        elif isinstance(stmt, OpcionStmt):
            if not self.table.scene_exists(stmt.target):
                self._error(
                    f"La opción apunta a la escena '{stmt.target}', "
                    f"pero esta escena no está definida en el programa",
                    stmt.line, stmt.col
                )
                self.log.fail(
                    'Referencia ir_a',
                    f"escena '{stmt.target}' no existe",
                    sc, stmt.line
                )
            else:
                self.log.ok(
                    'Referencia ir_a',
                    f"escena '{stmt.target}' existe",
                    sc, stmt.line
                )

        elif isinstance(stmt, AsignarStmt):
            self._analyze_expr(stmt.expr)
            if stmt.is_decl:
                if self.table.var_exists(sc, stmt.name):
                    self._error(
                        f"La variable '{stmt.name}' ya fue declarada en "
                        f"la escena '{sc}'",
                        stmt.line, stmt.col
                    )
                    self.log.fail(
                        'Declaración var',
                        f"var '{stmt.name}' ya existe en '{sc}'",
                        sc, stmt.line
                    )
                else:
                    self.table.add_var(sc, stmt.name, stmt.line, stmt.col)
                    self.log.ok(
                        'Declaración var',
                        f"var '{stmt.name}' declarada",
                        sc, stmt.line
                    )
            else:
                if not self.table.var_exists(sc, stmt.name):
                    self._error(
                        f"Variable '{stmt.name}' no declarada en la escena "
                        f"'{sc}'. Usa 'var {stmt.name} = ...'",
                        stmt.line, stmt.col
                    )
                    self.log.fail(
                        'Asignación var',
                        f"var '{stmt.name}' no declarada",
                        sc, stmt.line
                    )
                else:
                    self.log.ok(
                        'Asignación var',
                        f"var '{stmt.name}' existe, asignación válida",
                        sc, stmt.line
                    )

        elif isinstance(stmt, SiStmt):
            self._analyze_condition(stmt.condition)
            for s in stmt.then_body:
                self._analyze_stmt(s)
            if stmt.else_body:
                for s in stmt.else_body:
                    self._analyze_stmt(s)

    # ── Condición ─────────────────────────────────────────────────────────────

    def _analyze_condition(self, cond: Condition):
        self._analyze_expr(cond.left)
        self._analyze_expr(cond.right)
        self.log.ok(
            'Condición si',
            f"operandos válidos con op '{cond.op}'",
            self._current_scope, cond.line
        )

    # ── Expresiones ──────────────────────────────────────────────────────────

    def _analyze_expr(self, expr):
        sc = self._current_scope
        if isinstance(expr, VarExpr):
            if not self.table.var_exists(sc, expr.name):
                self._error(
                    f"Variable '{expr.name}' no declarada en la escena '{sc}'",
                    expr.line, expr.col
                )
                self.log.fail(
                    'Uso de variable',
                    f"var '{expr.name}' no declarada",
                    sc, expr.line
                )
            else:
                self.log.ok(
                    'Uso de variable',
                    f"var '{expr.name}' accedida correctamente",
                    sc, expr.line
                )
        elif isinstance(expr, ConcatExpr):
            self._analyze_expr(expr.left)
            self._analyze_expr(expr.right)

    # ── Utilidades ────────────────────────────────────────────────────────────

    def _error(self, msg: str, line: int, col: int):
        self.errors.append(SemanticError(msg, line, col))

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def print_errors(self):
        for e in self.errors:
            print(f"  [ERROR SEMÁNTICO] Línea {e.line}, Col {e.col}: {e}")
