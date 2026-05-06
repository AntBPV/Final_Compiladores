#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
#  run_tests.py  –  Ejecutor automático de las 20 pruebas del compilador
# ─────────────────────────────────────────────────────────────────────────────
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from lexer    import Lexer
from parser   import Parser
from semantic import SemanticAnalyzer
from codegen  import CodeGenerator


BASE = os.path.dirname(os.path.abspath(__file__))

TESTS_OK  = os.path.join(BASE, 'tests', 'exitosos')
TESTS_ERR = os.path.join(BASE, 'tests', 'errores')

GREEN  = '\033[92m'
RED    = '\033[91m'
YELLOW = '\033[93m'
CYAN   = '\033[96m'
BOLD   = '\033[1m'
RESET  = '\033[0m'

def run_compile(source: str):
    """Devuelve (codigo | None, [errores_lexicos], [errores_sint], [errores_sem])"""
    lexer  = Lexer(source)
    tokens = lexer.tokenize()
    if lexer.has_errors():
        return None, lexer.errors, [], []

    parser = Parser(tokens)
    ast    = parser.parse()
    if parser.has_errors():
        return None, [], parser.errors, []

    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    if analyzer.has_errors():
        return None, [], [], analyzer.errors

    gen  = CodeGenerator()
    code = gen.generate(ast)
    return code, [], [], []


def run_suite(folder: str, expect_success: bool):
    files = sorted(f for f in os.listdir(folder) if f.endswith('.gui'))
    passed = 0
    failed = 0

    for fname in files:
        path = os.path.join(folder, fname)
        with open(path, 'r', encoding='utf-8') as f:
            source = f.read()

        code, lex_err, syn_err, sem_err = run_compile(source)
        all_errors = lex_err + syn_err + sem_err
        success = (code is not None and not all_errors)

        # Leer primera línea como descripción
        first_line = source.strip().splitlines()[0].lstrip('/ ').strip()

        if expect_success:
            ok = success
            icon = f"{GREEN}✓ PASS{RESET}" if ok else f"{RED}✗ FAIL{RESET}"
        else:
            ok = not success
            icon = f"{GREEN}✓ PASS{RESET}" if ok else f"{RED}✗ FAIL{RESET}"

        print(f"  {icon}  {CYAN}{fname}{RESET}")
        print(f"         {YELLOW}{first_line}{RESET}")

        if all_errors:
            for e in all_errors:
                kind = 'LEX' if e in lex_err else ('SIN' if e in syn_err else 'SEM')
                col_val = getattr(e, 'column', getattr(e, 'col', '?'))
                print(f"         [{kind}] L{e.line}:C{col_val} → {e}")
        elif expect_success and not success:
            print(f"         Se esperaba éxito pero compiló con errores")

        if ok:
            passed += 1
        else:
            failed += 1
        print()

    return passed, failed


def main():
    print()
    print(f"{BOLD}{'═'*65}{RESET}")
    print(f"{BOLD}   SUITE DE PRUEBAS – Compilador de Guiones Interactivos{RESET}")
    print(f"{BOLD}{'═'*65}{RESET}\n")

    # ── Pruebas exitosas ──────────────────────────────────────────────────────
    print(f"{BOLD}{GREEN}━━━ PRUEBAS EXITOSAS (deben compilar sin errores) ━━━{RESET}\n")
    p1, f1 = run_suite(TESTS_OK, expect_success=True)

    # ── Pruebas de error ─────────────────────────────────────────────────────
    print(f"{BOLD}{RED}━━━ PRUEBAS CON ERRORES (deben detectar errores) ━━━━{RESET}\n")
    p2, f2 = run_suite(TESTS_ERR, expect_success=False)

    # ── Resumen ───────────────────────────────────────────────────────────────
    total   = p1 + f1 + p2 + f2
    pasadas = p1 + p2
    fallidas= f1 + f2

    print(f"{BOLD}{'═'*65}{RESET}")
    print(f"{BOLD}   RESUMEN FINAL{RESET}")
    print(f"{'─'*65}")
    print(f"   Pruebas exitosas  → {p1:>2} pasadas, {f1:>2} fallidas")
    print(f"   Pruebas de error  → {p2:>2} pasadas, {f2:>2} fallidas")
    print(f"{'─'*65}")
    color = GREEN if fallidas == 0 else RED
    print(f"   Total: {color}{pasadas}/{total} pruebas correctas{RESET}")
    print(f"{BOLD}{'═'*65}{RESET}\n")

    sys.exit(0 if fallidas == 0 else 1)


if __name__ == '__main__':
    main()
