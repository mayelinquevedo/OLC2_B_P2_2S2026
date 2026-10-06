import ply.yacc as yacc
from compiler.lexer.lexer import tokens
from compiler.errors import agregar_error
from compiler.ast.nodos import Programa, Function, Parametro, Bloque


# Regla inicial
def p_programa(p):
    'programa : lista_funciones'
    p[0] = Programa(p[1])


def p_lista_funciones_una(p):
    'lista_funciones : funcion'
    p[0] = [p[1]]


def p_lista_funciones_varias(p):
    'lista_funciones : lista_funciones funcion'
    p[0] = p[1] + [p[2]]


#Función
def p_funcion(p):
    'funcion : FN IDENTIFICADOR PAREN_IZQ lista_parametros_opt PAREN_DER tipo_retorno_opt bloque'
    p[0] = Function(
        nombre=p[2],
        parametros=p[4],
        tipo_retorno=p[6],
        cuerpo=p[7],
        linea=p.lineno(1)
    )


def p_tipo_retorno_opt_con(p):
    'tipo_retorno_opt : FLECHA tipo'
    p[0] = p[2]


def p_tipo_retorno_opt_vacio(p):
    'tipo_retorno_opt : empty'
    p[0] = None


def p_lista_parametros_opt_con(p):
    'lista_parametros_opt : lista_parametros'
    p[0] = p[1]


def p_lista_parametros_opt_vacio(p):
    'lista_parametros_opt : empty'
    p[0] = []


def p_lista_parametros_una(p):
    'lista_parametros : parametro'
    p[0] = [p[1]]


def p_lista_parametros_varias(p):
    'lista_parametros : lista_parametros COMA parametro'
    p[0] = p[1] + [p[3]]


def p_parametro(p):
    'parametro : IDENTIFICADOR DOS_PUNTOS tipo'
    p[0] = Parametro(nombre=p[1], tipo=p[3], linea=p.lineno(1))


def p_tipo(p):
    '''tipo : TIPO_I32
            | TIPO_F64
            | TIPO_BOOL
            | TIPO_CHAR
            | TIPO_STRING'''
    p[0] = p[1]


def p_bloque(p):
    'bloque : LLAVE_IZQ LLAVE_DER'
    p[0] = Bloque([], linea=p.lineno(1))

def p_empty(p):
    'empty :'
    pass

# Manejo de errores sintácticos 
def p_error(p):
    if p:
        agregar_error(
            "Sintactico",
            f"Error de sintaxis cerca de '{p.value}'",
            p.lineno
        )
    else:
        agregar_error("Sintactico", "Fin de archivo inesperado", 0)


parser = yacc.yacc()