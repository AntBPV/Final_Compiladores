# ─────────────────────────────────────────────────────────────
# Código generado automáticamente por el compilador de
# Guiones Interactivos
# ─────────────────────────────────────────────────────────────
import sys

_opciones_validas = set()

def portada():
    print("=== La Leyenda del Compilador ===")
    print("Una aventura épica de código y lógica")
    # Opción: 'Comenzar historia' → escena 'aldea'
    _opc = input("  > Comenzar historia: ").strip()
    if _opc.lower() in ('s', 'si', '1', 'ok', 'comenzar historia'):
        aldea()
        return

def aldea():
    valentia = 8
    print("Llegas a la aldea de Sintaxia.")
    print("El anciano te habla:")
    print(str("Tu valentía es: ") + str(valentia))
    if valentia >= 7:
        print("Eres digno de la mision, heroe!")
        # Opción: 'Aceptar misión' → escena 'fortaleza'
        _opc = input("  > Aceptar misión: ").strip()
        if _opc.lower() in ('s', 'si', '1', 'ok', 'aceptar misión'):
            fortaleza()
            return
    else:
        print("Aún no estás listo. Entrena más.")
        # Opción: 'Entrenar' → escena 'entrenamiento'
        _opc = input("  > Entrenar: ").strip()
        if _opc.lower() in ('s', 'si', '1', 'ok', 'entrenar'):
            entrenamiento()
            return

def entrenamiento():
    valentia = 10
    print(str("Después de entrenar, tu valentía es: ") + str(valentia))
    # Opción: 'Ir a la fortaleza' → escena 'fortaleza'
    _opc = input("  > Ir a la fortaleza: ").strip()
    if _opc.lower() in ('s', 'si', '1', 'ok', 'ir a la fortaleza'):
        fortaleza()
        return

def fortaleza():
    enemigos = 3
    print(str(str("La fortaleza tiene ") + str(enemigos)) + str(" guardianes."))
    if enemigos != 0:
        print("Debes derrotar a todos!")
        # Opción: 'Luchar' → escena 'victoria'
        _opc = input("  > Luchar: ").strip()
        if _opc.lower() in ('s', 'si', '1', 'ok', 'luchar'):
            victoria()
            return

def victoria():
    print("Ganaste! El compilador ha sido liberado!")
    print("FIN")

if __name__ == '__main__':
    print('=== Inicio del guion interactivo ===')
    portada()
    print('=== Fin del guion ===')
