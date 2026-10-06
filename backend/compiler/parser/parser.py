import ply.yacc as yacc
from compiler.lexer.lexer import tokens
from compiler.errors import agregar_error
from compiler.ast.nodos import (
    Programa, Function, Parametro, Bloque,
    DeclaracionVariable, Asignacion, Literal, Identificador,
    OperacionBinaria, OperacionUnaria
)

# Tabla de precedencia de operadores (de menor a mayor precedencia)
precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'IGUAL_IGUAL', 'DIFERENTE'),
    ('left', 'MAYORQUE', 'MENORQUE', 'MAYOR_IGUAL', 'MENOR_IGUAL'),
    ('left', 'MAS', 'MENOS'),
    ('left', 'MULT', 'DIV', 'MODULO'),
    ('right', 'NOT', 'UMENOS'),  
    
)


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


# Bloque de sentencias
def p_bloque(p):
    'bloque : LLAVE_IZQ lista_sentencias_opt LLAVE_DER'
    p[0] = Bloque(p[2], linea=p.lineno(1))


def p_lista_sentencias_opt_con(p):
    'lista_sentencias_opt : lista_sentencias'
    p[0] = p[1]


def p_lista_sentencias_opt_vacio(p):
    'lista_sentencias_opt : empty'
    p[0] = []


def p_lista_sentencias_una(p):
    'lista_sentencias : sentencia'
    p[0] = [p[1]] if p[1] is not None else []


def p_lista_sentencias_varias(p):
    'lista_sentencias : lista_sentencias sentencia'
    p[0] = p[1] + ([p[2]] if p[2] is not None else [])


def p_sentencia(p):
    '''sentencia : declaracion_variable
                  | asignacion
                  | error PUNTO_COMA'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = None

# Declaración de variable 
def p_declaracion_variable_con_tipo_y_valor(p):
    'declaracion_variable : LET mut_opt IDENTIFICADOR DOS_PUNTOS tipo IGUAL expresion PUNTO_COMA'
    p[0] = DeclaracionVariable(
        nombre=p[3], tipo=p[5], mutable=p[2], valor_inicial=p[7],
        linea=p.lineno(1)
    )


def p_declaracion_variable_solo_valor(p):
    'declaracion_variable : LET mut_opt IDENTIFICADOR IGUAL expresion PUNTO_COMA'
    p[0] = DeclaracionVariable(
        nombre=p[3], tipo=None, mutable=p[2], valor_inicial=p[5],
        linea=p.lineno(1)
    )


def p_declaracion_variable_solo_tipo(p):
    'declaracion_variable : LET mut_opt IDENTIFICADOR DOS_PUNTOS tipo PUNTO_COMA'
    p[0] = DeclaracionVariable(
        nombre=p[3], tipo=p[5], mutable=p[2], valor_inicial=None,
        linea=p.lineno(1)
    )


def p_declaracion_variable_sin_nada(p):
    'declaracion_variable : LET mut_opt IDENTIFICADOR PUNTO_COMA'
    p[0] = DeclaracionVariable(
        nombre=p[3], tipo=None, mutable=p[2], valor_inicial=None,
        linea=p.lineno(1)
    )


def p_mut_opt_con(p):
    'mut_opt : MUT'
    p[0] = True


def p_mut_opt_vacio(p):
    'mut_opt : empty'
    p[0] = False



# Asignación 
def p_asignacion(p):
    'asignacion : IDENTIFICADOR IGUAL expresion PUNTO_COMA'
    p[0] = Asignacion(nombre=p[1], operador='=', valor=p[3], linea=p.lineno(1))


# Expresiones 

def p_expresion_binaria(p):
    '''expresion : expresion MAS expresion
                  | expresion MENOS expresion
                  | expresion MULT expresion
                  | expresion DIV expresion
                  | expresion MODULO expresion
                  | expresion IGUAL_IGUAL expresion
                  | expresion DIFERENTE expresion
                  | expresion MAYORQUE expresion
                  | expresion MENORQUE expresion
                  | expresion MAYOR_IGUAL expresion
                  | expresion MENOR_IGUAL expresion
                  | expresion AND expresion
                  | expresion OR expresion'''
    p[0] = OperacionBinaria(p[1], p[2], p[3], linea=p.lineno(2))


def p_expresion_menos_unario(p):
    'expresion : MENOS expresion %prec UMENOS'
    p[0] = OperacionUnaria('-', p[2], linea=p.lineno(1))


def p_expresion_not(p):
    'expresion : NOT expresion'
    p[0] = OperacionUnaria('!', p[2], linea=p.lineno(1))


def p_expresion_agrupada(p):
    'expresion : PAREN_IZQ expresion PAREN_DER'
    p[0] = p[2]


def p_expresion_numero_entero(p):
    'expresion : NUMERO_ENTERO'
    p[0] = Literal(p[1], 'i32', linea=p.lineno(1))


def p_expresion_numero_decimal(p):
    'expresion : NUMERO_DECIMAL'
    p[0] = Literal(p[1], 'f64', linea=p.lineno(1))


def p_expresion_string(p):
    'expresion : STRING'
    p[0] = Literal(p[1], 'String', linea=p.lineno(1))


def p_expresion_char(p):
    'expresion : CHAR'
    p[0] = Literal(p[1], 'char', linea=p.lineno(1))


def p_expresion_true(p):
    'expresion : TRUE'
    p[0] = Literal(True, 'bool', linea=p.lineno(1))


def p_expresion_false(p):
    'expresion : FALSE'
    p[0] = Literal(False, 'bool', linea=p.lineno(1))


def p_expresion_identificador(p):
    'expresion : IDENTIFICADOR'
    p[0] = Identificador(p[1], linea=p.lineno(1))



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