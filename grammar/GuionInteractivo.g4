grammar GuionInteractivo;

// ─────────────────────────────────────────────
//  REGLAS SINTÁCTICAS
// ─────────────────────────────────────────────

program
    : (scene)+ EOF
    ;

scene
    : 'escena' ID '{' statement+ '}'
    ;

statement
    : decirStmt
    | opcionStmt
    | asignarStmt
    | siStmt
    ;

decirStmt
    : 'decir' expr ';'
    ;

opcionStmt
    : 'opcion' STRING 'ir_a' ID ';'
    ;

asignarStmt
    : 'var' ID '=' expr ';'
    | ID '=' expr ';'
    ;

siStmt
    : 'si' '(' condition ')' '{' statement+ '}'
      ('sino' '{' statement+ '}')?
    ;

condition
    : expr op=(EQUAL | NEQ | LT | GT | LTE | GTE) expr
    ;

expr
    : STRING                    # exprString
    | NUMBER                    # exprNumber
    | BOOL                      # exprBool
    | ID                        # exprVar
    | expr '+' expr             # exprConcat
    ;

// ─────────────────────────────────────────────
//  REGLAS LÉXICAS
// ─────────────────────────────────────────────

// Palabras clave
ESCENA  : 'escena' ;
DECIR   : 'decir' ;
OPCION  : 'opcion' ;
IR_A    : 'ir_a' ;
VAR     : 'var' ;
SI      : 'si' ;
SINO    : 'sino' ;
BOOL    : 'verdadero' | 'falso' ;

// Operadores de comparación
EQUAL   : '==' ;
NEQ     : '!=' ;
LT      : '<' ;
GT      : '>' ;
LTE     : '<=' ;
GTE     : '>=' ;

// Literales
STRING  : '"' (~["\r\n])* '"' ;
NUMBER  : [0-9]+ ('.' [0-9]+)? ;

// Identificadores
ID      : [a-zA-Z_áéíóúÁÉÍÓÚñÑ][a-zA-Z0-9_áéíóúÁÉÍÓÚñÑ]* ;

// Ignorar
WS      : [ \t\r\n]+ -> skip ;
COMMENT : '//' ~[\r\n]* -> skip ;
