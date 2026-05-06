# ─────────────────────────────────────────────────────────────────────────────
#  ast_nodes.py  –  Nodos del Árbol de Sintaxis Abstracta (AST)
# ─────────────────────────────────────────────────────────────────────────────
from dataclasses import dataclass, field
from typing import List, Optional, Any


@dataclass
class ASTNode:
    line: int = 0
    col:  int = 0


# ── Expresiones ───────────────────────────────────────────────────────────────

@dataclass
class StringLiteral(ASTNode):
    value: str = ''

@dataclass
class NumberLiteral(ASTNode):
    value: float = 0.0

@dataclass
class BoolLiteral(ASTNode):
    value: bool = False

@dataclass
class VarExpr(ASTNode):
    name: str = ''

@dataclass
class ConcatExpr(ASTNode):
    left:  Any = None   # Expr
    right: Any = None   # Expr


# ── Condición ─────────────────────────────────────────────────────────────────

@dataclass
class Condition(ASTNode):
    left:  Any = None   # Expr
    op:    str = ''
    right: Any = None   # Expr


# ── Sentencias ────────────────────────────────────────────────────────────────

@dataclass
class DecirStmt(ASTNode):
    expr: Any = None    # Expr

@dataclass
class OpcionStmt(ASTNode):
    label:  str = ''
    target: str = ''

@dataclass
class AsignarStmt(ASTNode):
    name:    str  = ''
    expr:    Any  = None
    is_decl: bool = False   # True si usa 'var'

@dataclass
class SiStmt(ASTNode):
    condition:  Any              = None
    then_body:  List[Any]        = field(default_factory=list)
    else_body:  Optional[List[Any]] = None


# ── Escena y Programa ─────────────────────────────────────────────────────────

@dataclass
class Scene(ASTNode):
    name:       str       = ''
    statements: List[Any] = field(default_factory=list)

@dataclass
class Program(ASTNode):
    scenes: List[Scene] = field(default_factory=list)
