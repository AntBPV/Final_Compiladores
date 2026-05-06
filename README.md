# Compilador de Guiones Interactivos
### Universidad Cooperativa de Colombia – Ingeniería de Software

---

## Descripción del Lenguaje

**Guiones Interactivos** (`.gui`) es un mini-lenguaje diseñado para crear
narrativas interactivas tipo "elige tu aventura". El compilador transforma
código fuente `.gui` en Python ejecutable, pasando por las cuatro fases
clásicas de un compilador.

---

## Especificación Formal del Lenguaje

### Gramática ANTLR4 (archivo `grammar/GuionInteractivo.g4`)

```antlr
program    : (scene)+ EOF ;
scene      : 'escena' ID '{' statement+ '}' ;
statement  : decirStmt | opcionStmt | asignarStmt | siStmt ;
decirStmt  : 'decir' expr ';' ;
opcionStmt : 'opcion' STRING 'ir_a' ID ';' ;
asignarStmt: 'var' ID '=' expr ';' | ID '=' expr ';' ;
siStmt     : 'si' '(' condition ')' '{' statement+ '}'
             ('sino' '{' statement+ '}')? ;
condition  : expr op expr ;
expr       : STRING | NUMBER | BOOL | ID | expr '+' expr ;
```

### Palabras reservadas

| Palabra    | Significado                        |
|------------|------------------------------------|
| `escena`   | Define un bloque/escena del guion  |
| `decir`    | Imprime texto o expresión          |
| `opcion`   | Presenta una opción al usuario     |
| `ir_a`     | Navega a otra escena               |
| `var`      | Declara una variable               |
| `si`       | Condicional if                     |
| `sino`     | Rama else del condicional          |
| `verdadero`| Literal booleano true              |
| `falso`    | Literal booleano false             |

### Tipos de datos

- **Texto**: cadenas entre comillas dobles `"Hola mundo"`
- **Número**: enteros y decimales `42`, `3.14`
- **Booleano**: `verdadero` / `falso`
- **Variable**: identificadores que comienzan con letra o `_`

### Operadores

| Operador | Descripción        |
|----------|--------------------|
| `+`      | Concatenación      |
| `==`     | Igual a            |
| `!=`     | Diferente de       |
| `<`      | Menor que          |
| `>`      | Mayor que          |
| `<=`     | Menor o igual      |
| `>=`     | Mayor o igual      |

### Reglas semánticas

1. Toda escena referenciada en `ir_a` debe estar definida en el programa.
2. Las variables deben declararse con `var` antes de usarse.
3. No se permite redeclarar una variable en la misma escena.
4. No se permite definir dos escenas con el mismo nombre.
5. Cada escena debe contener al menos una sentencia.

---

## Estructura del Proyecto

```
guiones_interactivos/
│
├── grammar/
│   └── GuionInteractivo.g4        ← Gramática ANTLR4 formal
│
├── src/
│   ├── lexer.py                   ← Fase 1: Análisis Léxico
│   ├── ast_nodes.py               ← Nodos del AST
│   ├── parser.py                  ← Fase 2: Análisis Sintáctico
│   ├── semantic.py                ← Fase 3: Análisis Semántico + Tabla de Símbolos
│   ├── codegen.py                 ← Fase 4: Generación de Código
│   └── compiler.py                ← Punto de entrada del compilador
│
├── tests/
│   ├── exitosos/                  ← 10 programas que deben compilar OK
│   └── errores/                   ← 10 programas con errores detectables
│
├── output/                        ← Código Python generado
└── run_tests.py                   ← Ejecutor automático de pruebas
```

---

## Fases del Compilador

### Fase 1 – Análisis Léxico (`lexer.py`)
Convierte el código fuente en una lista de **tokens**. Detecta:
- Caracteres desconocidos (e.g. `@`, `#`, `$`)
- Cadenas de texto sin cerrar

### Fase 2 – Análisis Sintáctico (`parser.py`)
Construye el **Árbol de Sintaxis Abstracta (AST)** aplicando descenso
recursivo. Detecta:
- Falta de `;` al final de sentencias
- Llaves `{` `}` sin cerrar
- Uso de `opcion` sin `ir_a`
- Escenas vacías
- Sentencias no reconocidas

### Fase 3 – Análisis Semántico (`semantic.py`)
Recorre el AST y valida la **tabla de símbolos**. Detecta:
- Referencias a escenas inexistentes
- Variables usadas sin declarar
- Variables declaradas dos veces en la misma escena
- Escenas duplicadas

### Fase 4 – Generación de Código (`codegen.py`)
Traduce el AST a un **script Python ejecutable**. Cada escena se convierte
en una función Python, y las opciones se traducen a `input()` + llamadas.

---

## Instalación y Uso

No se requieren dependencias externas. Solo Python 3.10+.

```bash
# Compilar un archivo y ver el código generado
python src/compiler.py ruta_a/mi_guion.gui

# Compilar y guardar el código Python
python src/compiler.py ruta_a/mi_guion.gui -o ruta_de/salida.py

# Compilar y ejecutar directamente
python src/compiler.py ruta_a/mi_guion.gui --run

# Ejecutar la suite de 20 pruebas
python run_tests.py
```

---

## Ejemplo Completo

**Entrada** (`inicio.gui`):
```
escena inicio {
    var jugador = "Héroe";
    decir "Bienvenido, " + jugador + "!";
    opcion "Comenzar aventura" ir_a bosque;
}

escena bosque {
    var peligro = 5;
    si (peligro > 3) {
        decir "El bosque es peligroso!";
        opcion "Huir" ir_a inicio;
    } sino {
        decir "El bosque es tranquilo.";
    }
}
```

**Salida Python generada**:
```python
def inicio():
    jugador = "Héroe"
    print(str("Bienvenido, ") + str(str(jugador) + str("!")))
    _opc = input("  > Comenzar aventura: ").strip()
    if _opc.lower() in ('s', 'si', '1', 'ok', 'comenzar aventura'):
        bosque()
        return

def bosque():
    peligro = 5
    if peligro > 3:
        print("El bosque es peligroso!")
        _opc = input("  > Huir: ").strip()
        if _opc.lower() in ('s', 'si', '1', 'ok', 'huir'):
            inicio()
            return
    else:
        print("El bosque es tranquilo.")

if __name__ == '__main__':
    print('=== Inicio del guion interactivo ===')
    inicio()
    print('=== Fin del guion ===')
```

---

## Tabla de Pruebas

### Pruebas Exitosas (10)

| # | Archivo | Característica probada |
|---|---------|----------------------|
| 1 | `prueba01_flujo_basico.gui` | Flujo básico de escenas conectadas |
| 2 | `prueba02_variables.gui` | Declaración y uso de variables + concatenación |
| 3 | `prueba03_condicionales.gui` | Condicionales `si`/`sino` |
| 4 | `prueba04_booleanos.gui` | Variables y comparación booleana |
| 5 | `prueba05_multiples_opciones.gui` | Múltiples opciones en una escena |
| 6 | `prueba06_comparaciones.gui` | Operadores `>`, `<`, `>=`, `<=` |
| 7 | `prueba07_reasignacion.gui` | Reasignación de variables |
| 8 | `prueba08_comentarios.gui` | Comentarios `//` ignorados |
| 9 | `prueba09_desigualdad.gui` | Operador `!=` |
|10 | `prueba10_historia_completa.gui` | Historia completa multi-escena |

### Pruebas con Errores (10)

| # | Archivo | Tipo de error | Descripción |
|---|---------|--------------|-------------|
| 1 | `error01_lexico_caracter.gui` | **LÉXICO** | Carácter `@` desconocido |
| 2 | `error02_lexico_cadena.gui` | **LÉXICO** | Cadena sin comilla de cierre |
| 3 | `error03_lexico_simbolos.gui` | **LÉXICO** | Símbolos `#` y `$` inválidos |
| 4 | `error04_sintactico_semicolon.gui` | **SINTÁCTICO** | Falta `;` en `decir` |
| 5 | `error05_sintactico_llave.gui` | **SINTÁCTICO** | Falta `}` de cierre |
| 6 | `error06_sintactico_ira.gui` | **SINTÁCTICO** | Falta `ir_a` en `opcion` |
| 7 | `error07_sintactico_escena_vacia.gui` | **SINTÁCTICO** | Escena sin sentencias |
| 8 | `error08_semantico_escena_inexistente.gui` | **SEMÁNTICO** | Referencia a escena no definida |
| 9 | `error09_semantico_variable_nodeclarada.gui` | **SEMÁNTICO** | Variable sin `var` |
|10 | `error10_semantico_duplicados.gui` | **SEMÁNTICO** | Escena y variable duplicadas |

---

*Universidad Cooperativa de Colombia – Ingeniería de Software*
*Proyecto: Mini-compilador de Guiones Interactivos*
