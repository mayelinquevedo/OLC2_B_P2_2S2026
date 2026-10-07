import ply.yacc as yacc
from compiler.lexer.lexer import tokens
from compiler.errors import agregar_error
from compiler.ast.nodos import (
    Programa, Function, Parametro, Bloque,
    DeclaracionVariable, Asignacion, Literal, Identificador,
    OperacionBinaria, OperacionUnaria,
    If, While, Loop, Match, CasoMatch,
    Break, Continue, Return, LlamadaPrintln, LlamadaFuncion
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
                  | if_stmt
                  | while_stmt
                  | loop_stmt
                  | match_stmt
                  | break_stmt
                  | continue_stmt
                  | return_stmt
                  | println_stmt
                  | llamada_funcion_stmt
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


# if / else 
def p_if_stmt_sin_else(p):
    'if_stmt : IF expresion bloque'
    p[0] = If(condicion=p[2], bloque_entonces=p[3], bloque_sino=None, linea=p.lineno(1))


def p_if_stmt_con_else(p):
    'if_stmt : IF expresion bloque ELSE bloque'
    p[0] = If(condicion=p[2], bloque_entonces=p[3], bloque_sino=p[5], linea=p.lineno(1))


def p_if_stmt_else_if(p):
    'if_stmt : IF expresion bloque ELSE if_stmt'
    p[0] = If(condicion=p[2], bloque_entonces=p[3], bloque_sino=Bloque([p[5]]), linea=p.lineno(1))


# while 
def p_while_stmt(p):
    'while_stmt : WHILE expresion bloque'
    p[0] = While(condicion=p[2], bloque=p[3], linea=p.lineno(1))


# loop 
def p_loop_stmt_sin_etiqueta(p):
    'loop_stmt : LOOP bloque'
    p[0] = Loop(bloque=p[2], etiqueta=None, linea=p.lineno(1))


def p_loop_stmt_con_etiqueta(p):
    'loop_stmt : ETIQUETA DOS_PUNTOS LOOP bloque'
    p[0] = Loop(bloque=p[4], etiqueta=p[1], linea=p.lineno(1))



# match 
def p_match_stmt(p):
    'match_stmt : MATCH expresion LLAVE_IZQ lista_casos LLAVE_DER'
    p[0] = Match(expresion=p[2], casos=p[4], linea=p.lineno(1))


def p_lista_casos_uno(p):
    'lista_casos : caso'
    p[0] = [p[1]]


def p_lista_casos_varios(p):
    'lista_casos : lista_casos caso'
    p[0] = p[1] + [p[2]]


def p_caso_expresion(p):
    'caso : expresion FLECHA_MATCH bloque_o_expresion COMA'
    p[0] = CasoMatch(patron=p[1], bloque=p[3], linea=p.lineno(1))


def p_caso_comodin(p):
    'caso : IDENTIFICADOR FLECHA_MATCH bloque_o_expresion COMA'
    if p[1] != '_':
        agregar_error("Sintactico", f"Se esperaba un patron valido o '_', se obtuvo '{p[1]}'", p.lineno(1))
    p[0] = CasoMatch(patron=None, bloque=p[3], linea=p.lineno(1))


def p_bloque_o_expresion_bloque(p):
    'bloque_o_expresion : bloque'
    p[0] = p[1]


def p_bloque_o_expresion_expr(p):
    'bloque_o_expresion : expresion'
    p[0] = Bloque([p[1]], linea=p.lineno(1))



# break / continue / return 
def p_break_sin_etiqueta(p):
    'break_stmt : BREAK PUNTO_COMA'
    p[0] = Break(etiqueta=None, linea=p.lineno(1))


def p_break_con_etiqueta(p):
    'break_stmt : BREAK ETIQUETA PUNTO_COMA'
    p[0] = Break(etiqueta=p[2], linea=p.lineno(1))


def p_continue_sin_etiqueta(p):
    'continue_stmt : CONTINUE PUNTO_COMA'
    p[0] = Continue(etiqueta=None, linea=p.lineno(1))


def p_continue_con_etiqueta(p):
    'continue_stmt : CONTINUE ETIQUETA PUNTO_COMA'
    p[0] = Continue(etiqueta=p[2], linea=p.lineno(1))


def p_return_sin_valor(p):
    'return_stmt : RETURN PUNTO_COMA'
    p[0] = Return(valor=None, linea=p.lineno(1))


def p_return_con_valor(p):
    'return_stmt : RETURN expresion PUNTO_COMA'
    p[0] = Return(valor=p[2], linea=p.lineno(1))


# println! 
def p_println_stmt(p):
    'println_stmt : IDENTIFICADOR NOT PAREN_IZQ STRING args_opt PAREN_DER PUNTO_COMA'
    if p[1] != 'println':
        agregar_error("Sintactico", f"Funcion embebida desconocida '{p[1]}!'", p.lineno(1))
    p[0] = LlamadaPrintln(formato=p[4], argumentos=p[5], linea=p.lineno(1))


def p_args_opt_con(p):
    'args_opt : COMA lista_argumentos'
    p[0] = p[2]


def p_args_opt_vacio(p):
    'args_opt : empty'
    p[0] = []


def p_lista_argumentos_uno(p):
    'lista_argumentos : expresion'
    p[0] = [p[1]]


def p_lista_argumentos_varios(p):
    'lista_argumentos : lista_argumentos COMA expresion'
    p[0] = p[1] + [p[3]]


# Llamada a función como sentencia 
def p_llamada_funcion_stmt(p):
    'llamada_funcion_stmt : IDENTIFICADOR PAREN_IZQ lista_argumentos_opt PAREN_DER PUNTO_COMA'
    p[0] = LlamadaFuncion(nombre=p[1], argumentos=p[3], linea=p.lineno(1))


def p_lista_argumentos_opt_con(p):
    'lista_argumentos_opt : lista_argumentos'
    p[0] = p[1]


def p_lista_argumentos_opt_vacio(p):
    'lista_argumentos_opt : empty'
    p[0] = []

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

def p_expresion_llamada_funcion(p):
    'expresion : IDENTIFICADOR PAREN_IZQ lista_argumentos_opt PAREN_DER'
    p[0] = LlamadaFuncion(nombre=p[1], argumentos=p[3], linea=p.lineno(1))

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