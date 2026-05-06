# ─────────────────────────────────────────────────────────────────────────────
#  codegen.py  –  Generador de Código Intermedio → Python ejecutable
# ─────────────────────────────────────────────────────────────────────────────
from ast_nodes import (
    Program, Scene,
    DecirStmt, OpcionStmt, AsignarStmt, SiStmt,
    Condition,
    StringLiteral, NumberLiteral, BoolLiteral, VarExpr, ConcatExpr,
)


class CodeGenerator:
    INDENT = '    '

    def __init__(self):
        self._lines: list[str] = []
        self._scene_names: list[str] = []

    # ── API pública ──────────────────────────────────────────────────────────

    def generate(self, program: Program) -> str:
        self._lines = []
        self._scene_names = [s.name for s in program.scenes]

        self._emit_header()
        for scene in program.scenes:
            self._gen_scene(scene)
        self._emit_entry_point(program)

        return '\n'.join(self._lines)

    # ── Cabecera ──────────────────────────────────────────────────────────────

    def _emit_header(self):
        self._lines += [
            "# ─────────────────────────────────────────────────────────────",
            "# Código generado automáticamente por el compilador de",
            "# Guiones Interactivos",
            "# ─────────────────────────────────────────────────────────────",
            "import sys",
            "",
            "_opciones_validas = set()",
            "",
        ]

    # ── Escenas ───────────────────────────────────────────────────────────────

    def _gen_scene(self, scene: Scene):
        self._lines.append(f"def {scene.name}():")
        if not scene.statements:
            self._lines.append(f"{self.INDENT}pass")
        else:
            for stmt in scene.statements:
                self._gen_stmt(stmt, depth=1)
        self._lines.append("")

    # ── Sentencias ────────────────────────────────────────────────────────────

    def _gen_stmt(self, stmt, depth: int):
        pad = self.INDENT * depth

        if isinstance(stmt, DecirStmt):
            expr_code = self._gen_expr(stmt.expr)
            self._lines.append(f"{pad}print({expr_code})")

        elif isinstance(stmt, OpcionStmt):
            label = stmt.label.replace('"', '\\"')
            target = stmt.target
            self._lines += [
                f"{pad}# Opción: '{label}' → escena '{target}'",
                f"{pad}_opc = input(\"  > {label}: \").strip()",
                f"{pad}if _opc.lower() in ('s', 'si', '1', 'ok', '{label.lower()}'):",
                f"{pad}{self.INDENT}{target}()",
                f"{pad}{self.INDENT}return",
            ]

        elif isinstance(stmt, AsignarStmt):
            expr_code = self._gen_expr(stmt.expr)
            self._lines.append(f"{pad}{stmt.name} = {expr_code}")

        elif isinstance(stmt, SiStmt):
            cond_code = self._gen_condition(stmt.condition)
            self._lines.append(f"{pad}if {cond_code}:")
            for s in stmt.then_body:
                self._gen_stmt(s, depth + 1)
            if stmt.else_body:
                self._lines.append(f"{pad}else:")
                for s in stmt.else_body:
                    self._gen_stmt(s, depth + 1)

    # ── Condiciones ───────────────────────────────────────────────────────────

    def _gen_condition(self, cond: Condition) -> str:
        left  = self._gen_expr(cond.left)
        right = self._gen_expr(cond.right)
        op_map = {'==': '==', '!=': '!=', '<': '<', '>': '>', '<=': '<=', '>=': '>='}
        op = op_map.get(cond.op, cond.op)
        return f"{left} {op} {right}"

    # ── Expresiones ──────────────────────────────────────────────────────────

    def _gen_expr(self, expr) -> str:
        if isinstance(expr, StringLiteral):
            escaped = expr.value.replace('\\', '\\\\').replace('"', '\\"')
            return f'"{escaped}"'
        if isinstance(expr, NumberLiteral):
            v = expr.value
            return str(int(v)) if v == int(v) else str(v)
        if isinstance(expr, BoolLiteral):
            return 'True' if expr.value else 'False'
        if isinstance(expr, VarExpr):
            return expr.name
        if isinstance(expr, ConcatExpr):
            left  = self._gen_expr(expr.left)
            right = self._gen_expr(expr.right)
            return f"str({left}) + str({right})"
        return '""'

    # ── Punto de entrada ──────────────────────────────────────────────────────

    def _emit_entry_point(self, program: Program):
        first = program.scenes[0].name if program.scenes else None
        self._lines += [
            "if __name__ == '__main__':",
            f"{self.INDENT}print('=== Inicio del guion interactivo ===')",
        ]
        if first:
            self._lines.append(f"{self.INDENT}{first}()")
        self._lines += [
            f"{self.INDENT}print('=== Fin del guion ===')",
            "",
        ]
