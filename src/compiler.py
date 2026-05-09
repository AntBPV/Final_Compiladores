#!/usr/bin/env python3
import sys, os, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lexer    import Lexer, TokenType
from parser   import Parser
from semantic import SemanticAnalyzer
from codegen  import CodeGenerator
from ast_nodes import (
    Program, Scene,
    DecirStmt, OpcionStmt, AsignarStmt, SiStmt,
    Condition,
    StringLiteral, NumberLiteral, BoolLiteral, VarExpr, ConcatExpr,
)

_SKIP_DISPLAY = {TokenType.EOF}

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║   Compilador de Guiones Interactivos  v1.0                   ║
║   Universidad Cooperativa de Colombia - Ingeniería Software  ║
╚══════════════════════════════════════════════════════════════╝"""


# ── Impresión de tokens ───────────────────────────────────────────────────────

def print_tokens(tokens):
    visible = [t for t in tokens if t.type not in _SKIP_DISPLAY]
    col_w = max((len(t.type) for t in visible), default=10) + 2
    val_w = max((len(repr(t.value)) for t in visible), default=8) + 2
    col_w = max(col_w, 16)
    val_w = max(val_w, 10)

    top = f"  ┌{'─'*col_w}┬{'─'*val_w}┬{'─'*8}┬{'─'*8}┐"
    hdr = f"  │ {'TIPO':<{col_w-2}} │ {'VALOR':<{val_w-2}} │ {'LÍNEA':<6} │ {'COL':<6} │"
    mid = f"  ╞{'═'*col_w}╪{'═'*val_w}╪{'═'*8}╪{'═'*8}╡"
    sep = f"  ├{'─'*col_w}┼{'─'*val_w}┼{'─'*8}┼{'─'*8}┤"
    bot = f"  └{'─'*col_w}┴{'─'*val_w}┴{'─'*8}┴{'─'*8}┘"

    print(top); print(hdr); print(mid)
    for i, tok in enumerate(visible):
        vr = repr(tok.value) if tok.value else '""'
        print(f"  │ {tok.type:<{col_w-2}} │ {vr:<{val_w-2}} │ {tok.line:<6} │ {tok.column:<6} │")
        if i < len(visible) - 1:
            print(sep)
    print(bot)
    print(f"  Total: {len(visible)} token(s) generado(s)\n")


# ── Impresión del AST ─────────────────────────────────────────────────────────

def _expr_str(expr) -> str:
    if isinstance(expr, StringLiteral):  return f'"{expr.value}"'
    if isinstance(expr, NumberLiteral):
        v = expr.value
        return str(int(v)) if v == int(v) else str(v)
    if isinstance(expr, BoolLiteral):    return 'verdadero' if expr.value else 'falso'
    if isinstance(expr, VarExpr):        return f'VAR({expr.name})'
    if isinstance(expr, ConcatExpr):     return f'CONCAT({_expr_str(expr.left)} + {_expr_str(expr.right)})'
    return '?'

def _cond_str(cond) -> str:
    return f'{_expr_str(cond.left)} {cond.op} {_expr_str(cond.right)}'

def _print_stmt(stmt, prefix: str, is_last: bool):
    conn       = '└─' if is_last else '├─'
    child_pref = prefix + ('   ' if is_last else '│  ')

    if isinstance(stmt, DecirStmt):
        print(f"{prefix}{conn} [DECIR]   expr = {_expr_str(stmt.expr)}   (L{stmt.line})")

    elif isinstance(stmt, OpcionStmt):
        print(f"{prefix}{conn} [OPCION]  label = \"{stmt.label}\"  →  destino: {stmt.target}   (L{stmt.line})")

    elif isinstance(stmt, AsignarStmt):
        kw = 'VAR' if stmt.is_decl else 'ASIG'
        print(f"{prefix}{conn} [{kw}]     {stmt.name} = {_expr_str(stmt.expr)}   (L{stmt.line})")

    elif isinstance(stmt, SiStmt):
        print(f"{prefix}{conn} [SI]      cond = ({_cond_str(stmt.condition)})   (L{stmt.line})")
        has_else   = bool(stmt.else_body)
        print(f"{child_pref}├─ [ENTONCES]")
        then_pref = child_pref + '│  '
        for j, s in enumerate(stmt.then_body):
            _print_stmt(s, then_pref, j == len(stmt.then_body) - 1)
        if has_else:
            print(f"{child_pref}└─ [SINO]")
            else_pref = child_pref + '   '
            for j, s in enumerate(stmt.else_body):
                _print_stmt(s, else_pref, j == len(stmt.else_body) - 1)

def print_ast(program: Program):
    print(f"  Program  [{len(program.scenes)} escena(s)]")
    for i, scene in enumerate(program.scenes):
        last_sc  = (i == len(program.scenes) - 1)
        sc_conn  = '└─' if last_sc else '├─'
        sc_pref  = '     ' if last_sc else '  │  '
        print(f"  {sc_conn} [ESCENA]  nombre = \"{scene.name}\"  |  sentencias = {len(scene.statements)}   (L{scene.line})")
        for j, stmt in enumerate(scene.statements):
            _print_stmt(stmt, f"  {sc_pref}", j == len(scene.statements) - 1)
    print()


# ── Pipeline del compilador ───────────────────────────────────────────────────

def compile_source(source: str, filename: str = '<stdin>'):

    # FASE 1
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  FASE 1  ·  ANÁLISIS LÉXICO                                  ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"  Archivo : {filename}")
    print(f"  Líneas  : {len(source.splitlines())}\n")

    lexer  = Lexer(source)
    tokens = lexer.tokenize()

    if lexer.has_errors():
        print(f"  ✗ {len(lexer.errors)} error(es) léxico(s):\n")
        lexer.print_errors()
        print("\n  ✗ Compilación detenida — errores léxicos.\n")
        return None, False

    print("  ✓ Tokenización completada sin errores\n")
    print("  TABLA DE TOKENS:")
    print_tokens(tokens)

    # FASE 2
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  FASE 2  ·  ANÁLISIS SINTÁCTICO                              ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")

    parser = Parser(tokens)
    ast    = parser.parse()

    if parser.has_errors():
        print(f"  ✗ {len(parser.errors)} error(es) sintáctico(s):\n")
        parser.print_errors()
        print("\n  ✗ Compilación detenida — errores sintácticos.\n")
        return None, False

    total_stmts = sum(len(s.statements) for s in ast.scenes)
    print(f"  ✓ AST construido correctamente")
    print(f"    Escenas detectadas  : {len(ast.scenes)}")
    print(f"    Sentencias totales  : {total_stmts}\n")
    print("  ÁRBOL DE SINTAXIS ABSTRACTA (AST):")
    print_ast(ast)

    # FASE 3
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  FASE 3  ·  ANÁLISIS SEMÁNTICO                               ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")

    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)

    if analyzer.has_errors():
        print(f"  ✗ {len(analyzer.errors)} error(es) semántico(s):\n")
        analyzer.print_errors()
        print()
        print("  REGISTRO DE VERIFICACIONES SEMÁNTICAS:")
        print(analyzer.log.dump())
        print("\n  ✗ Compilación detenida — errores semánticos.\n")
        return None, False

    print("  ✓ Análisis semántico completado sin errores\n")
    print("  REGISTRO DE VERIFICACIONES SEMÁNTICAS:")
    print(analyzer.log.dump())
    print("  TABLA DE SÍMBOLOS:")
    print(analyzer.table.dump())
    print()

    # FASE 4
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  FASE 4  ·  GENERACIÓN DE CÓDIGO                             ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")

    gen  = CodeGenerator()
    code = gen.generate(ast)

    funcs = code.count('\ndef ')
    lines = len(code.splitlines())
    print(f"  ✓ Código Python generado exitosamente")
    print(f"    Funciones generadas : {funcs}")
    print(f"    Líneas de código    : {lines}\n")
    print("  CÓDIGO PYTHON GENERADO:")
    print("  " + "─" * 60)
    for ln in code.splitlines():
        print(f"  {ln}")
    print("  " + "─" * 60)
    print()

    return code, True


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(BANNER)
    ap = argparse.ArgumentParser(description='Compilador de Guiones Interactivos')
    ap.add_argument('file',           help='Archivo fuente .gui')
    ap.add_argument('-o', '--output', help='Guardar Python generado en archivo', default=None)
    ap.add_argument('--run',          help='Ejecutar tras compilar', action='store_true')
    args = ap.parse_args()

    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            source = f.read()
    except FileNotFoundError:
        print(f"\n  ✗ Archivo no encontrado: {args.file}\n")
        sys.exit(1)

    print(f"\n  Compilando : {args.file}\n")
    code, success = compile_source(source, args.file)

    if not success:
        sys.exit(1)

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  COMPILACIÓN EXITOSA  ✓                                      ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(code)
        print(f"  Código guardado en: {args.output}\n")

    if args.run:
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║  EJECUCIÓN                                                    ║")
        print("╚══════════════════════════════════════════════════════════════╝\n")
        exec(compile(code, args.file, 'exec'), {'__name__': '__main__'})

    sys.exit(0)


if __name__ == '__main__':
    main()
