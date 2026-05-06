# ─────────────────────────────────────────────────────────────
# Código generado automáticamente por el compilador de
# Guiones Interactivos
# ─────────────────────────────────────────────────────────────
import sys

_opciones_validas = set()

def inicio():
    print("Bienvenido al guion interactivo!")
    # Opción: 'Comenzar aventura' → escena 'juego'
    _opc = input("  > Comenzar aventura: ").strip()
    if _opc.lower() in ('s', 'si', '1', 'ok', 'comenzar aventura'):
        juego()
        return

def juego():
    print("Estas en el nivel 1. Prepárate!")
    # Opción: 'Continuar' → escena 'fin'
    _opc = input("  > Continuar: ").strip()
    if _opc.lower() in ('s', 'si', '1', 'ok', 'continuar'):
        fin()
        return

def fin():
    print("Has completado el guion. Gracias por jugar!")

if __name__ == '__main__':
    print('=== Inicio del guion interactivo ===')
    inicio()
    print('=== Fin del guion ===')
