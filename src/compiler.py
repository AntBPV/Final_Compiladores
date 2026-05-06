#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
#  compiler.py  –  Punto de entrada del compilador de Guiones Interactivos
#
#  Uso:
#    python compiler.py <archivo.gui>              # compila y muestra código
#    python compiler.py <archivo.gui> -o salida.py # compila y guarda
#    python compiler.py <archivo.gui> --run        # compila y ejecuta
# ─────────────────────────────────────────────────────────────────────────────
import sys
import os
import argparse

# Asegura que src/ esté en el path cuando se invoca desde fuera
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lexer    import Lexer
from parser   import Parser
from semantic import SemanticAnalyzer
from codegen  import CodeGenerator


BANNER = """
╔══════════════════════════════════════════════════════════════╗
║   Compilador de Guiones Interactivos  v1.0                   ║
║   Universidad Cooperativa de Colombia – Ingeniería Software  ║
╚══════════════════════════════════════════════════════════════╝
"""


def compile_source(source: str, filename: str = '<stdin>',
                   verbose: bool = True) -> tuple[str | None, bool]:
    """
    Ejecuta todas las fases del compilador.
    Devuelve (codigo_python | None, exito).
    """
    ok = True

    # ── FASE 1: Análisis Léxico ─────────────────────────────────────────────
    if verbose:
        print("─── FASE 1: Análisis Léxico ───────────────────────────────")
    lexer  = Lexer(source)
    tokens = lexer.tokenize()

    if lexer.has_errors():
        print(f"  Se encontraron {len(lexer.errors)} error(es) léxico(s):")
        lexer.print_errors()
        ok = False
    else:
        if verbose:
            print(f"  ✓ {len(tokens)-1} tokens generados sin errores")

    # ── FASE 2: Análisis Sintáctico ─────────────────────────────────────────
    if verbose:
        print("─── FASE 2: Análisis Sintáctico ───────────────────────────")
    parser = Parser(tokens)
    ast    = parser.parse()

    if parser.has_errors():
        print(f"  Se encontraron {len(parser.errors)} error(es) sintáctico(s):")
        parser.print_errors()
        ok = False
    else:
        if verbose:
            print(f"  ✓ AST construido: {len(ast.scenes)} escena(s)")

    if not ok:
        print("\n✗ Compilación detenida por errores léxicos/sintácticos.\n")
        return None, False

    # ── FASE 3: Análisis Semántico ──────────────────────────────────────────
    if verbose:
        print("─── FASE 3: Análisis Semántico ────────────────────────────")
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)

    if analyzer.has_errors():
        print(f"  Se encontraron {len(analyzer.errors)} error(es) semántico(s):")
        analyzer.print_errors()
        ok = False
    else:
        if verbose:
            print("  ✓ Análisis semántico completado sin errores")

    if verbose:
        print()
        print(analyzer.table.dump())

    if not ok:
        print("\n✗ Compilación detenida por errores semánticos.\n")
        return None, False

    # ── FASE 4: Generación de Código ────────────────────────────────────────
    if verbose:
        print("─── FASE 4: Generación de Código ──────────────────────────")
    gen  = CodeGenerator()
    code = gen.generate(ast)

    if verbose:
        print("  ✓ Código Python generado exitosamente\n")

    return code, True


def main():
    print(BANNER)
    ap = argparse.ArgumentParser(
        description='Compilador de Guiones Interactivos (.gui → Python)'
    )
    ap.add_argument('file',           help='Archivo fuente .gui')
    ap.add_argument('-o', '--output', help='Archivo de salida Python', default=None)
    ap.add_argument('--run',          help='Ejecutar tras compilar', action='store_true')
    ap.add_argument('-v', '--verbose',help='Modo detallado', action='store_true', default=True)
    args = ap.parse_args()

    # Leer fuente
    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            source = f.read()
    except FileNotFoundError:
        print(f"✗ Archivo no encontrado: {args.file}")
        sys.exit(1)

    print(f"Compilando: {args.file}\n")
    code, success = compile_source(source, args.file, verbose=args.verbose)

    if not success:
        sys.exit(1)

    # Mostrar o guardar
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(code)
        print(f"✓ Código guardado en: {args.output}")
    else:
        print("─── Código Python generado ────────────────────────────────")
        print(code)

    # Ejecutar
    if args.run:
        print("─── Ejecución ─────────────────────────────────────────────")
        exec(compile(code, args.file, 'exec'), {'__name__': '__main__'})

    sys.exit(0)


if __name__ == '__main__':
    main()
