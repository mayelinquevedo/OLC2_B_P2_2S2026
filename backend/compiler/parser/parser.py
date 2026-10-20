import ply.yacc as yacc
from compiler.lexer.lexer import tokens
from compiler.errors import agregar_error, encontrar_columna
from compiler.ast.nodos import (
    Programa, Function, Parametro, Bloque,
    DeclaracionVariable, Asignacion, Literal, Identificador,
    OperacionBinaria, OperacionUnaria,
    If, While, Loop, Match, CasoMatch,
    Break, Continue, Return, LlamadaPrintln, LlamadaFuncion,
    Arreglo, AccesoIndice, Slice, LlamadaMetodo
)

def col(p, n):
    """Columna del simbolo n de la regla (solo funciona con terminales)."""
    return encontrar_columna(p.lexer.lexdata, p.lexpos(n))


def pos(p, n):
    return {'linea': p.lineno(n), 'columna': col(p, n)}

# Tabla de precedencia de operadores (de menor a mayor precedencia)
precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'IGUAL_IGUAL', 'DIFERENTE'),
    ('left', 'MAYORQUE', 'MENORQUE', 'MAYOR_IGUAL', 'MENOR_IGUAL'),
    ('left', 'MAS', 'MENOS'),
    ('left', 'MULT', 'DIV', 'MODULO'),
    ('right', 'NOT', 'UMENOS'),  
    ('left', 'CORCH_IZQ', 'PUNTO'),
    
)


# Regla inicial
def p_programa(p):
    'programa : lista_funciones'
    p[0] = Programa(p[1], linea=1, columna=1)


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
        **pos(p, 1)
    )



def p_tipo_retorno_opt_con(p):
    'tipo_retorno_opt : FLECHA tipo'
    p[0] = p[2]


def p_tipo_retorno_opt_vacio(p):
    'tipo_retorno_opt : empty'
    p[0] = None

def p_tipo_arreglo(p):
    'tipo : CORCH_IZQ tipo PUNTO_COMA NUMERO_ENTERO CORCH_DER'
    p[0] = f"[{p[2]}; {p[4]}]"

def p_tipo_slice(p):
    'tipo : AMPER CORCH_IZQ tipo CORCH_DER'
    p[0] = f"&[{p[3]}]"


def p_tipo_vec_str(p):
    'tipo : IDENTIFICADOR MENORQUE AMPER IDENTIFICADOR MAYORQUE'
    if p[1] != 'Vec' or p[4] != 'str':
        agregar_error("Sintactico", f"Tipo desconocido '{p[1]}<&{p[4]}>'", p.lineno(1), col(p, 1))
    p[0] = "&[String]"

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
    p[0] = Parametro(nombre=p[1], tipo=p[3], **pos(p, 1))


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
    p[0] = Bloque(p[2], **pos(p, 1))


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
                  | error PUNTO_COMA'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = None

def p_sentencia_expresion(p):
    'sentencia : expresion PUNTO_COMA'
    p[0] = p[1]

# Declaración de variable 
def p_declaracion_variable_con_tipo_y_valor(p):
    'declaracion_variable : LET mut_opt IDENTIFICADOR DOS_PUNTOS tipo IGUAL expresion PUNTO_COMA'
    p[0] = DeclaracionVariable(
        nombre=p[3], tipo=p[5], mutable=p[2], valor_inicial=p[7],
        **pos(p, 1)
    )


def p_declaracion_variable_solo_valor(p):
    'declaracion_variable : LET mut_opt IDENTIFICADOR IGUAL expresion PUNTO_COMA'
    p[0] = DeclaracionVariable(
        nombre=p[3], tipo=None, mutable=p[2], valor_inicial=p[5],
        **pos(p, 1)
    )


def p_declaracion_variable_solo_tipo(p):
    'declaracion_variable : LET mut_opt IDENTIFICADOR DOS_PUNTOS tipo PUNTO_COMA'
    p[0] = DeclaracionVariable(
        nombre=p[3], tipo=p[5], mutable=p[2], valor_inicial=None,
        **pos(p, 1)
    )


def p_declaracion_variable_sin_nada(p):
    'declaracion_variable : LET mut_opt IDENTIFICADOR PUNTO_COMA'
    p[0] = DeclaracionVariable(
        nombre=p[3], tipo=None, mutable=p[2], valor_inicial=None,
        **pos(p, 1)
    )


def p_mut_opt_con(p):
    'mut_opt : MUT'
    p[0] = True


def p_mut_opt_vacio(p):
    'mut_opt : empty'
    p[0] = False



# Asignación 
def p_asignacion(p):
    '''asignacion : expresion IGUAL expresion PUNTO_COMA
                   | expresion MAS_IGUAL expresion PUNTO_COMA
                   | expresion MENOS_IGUAL expresion PUNTO_COMA
                   | expresion MULT_IGUAL expresion PUNTO_COMA
                   | expresion DIV_IGUAL expresion PUNTO_COMA
                   | expresion MODULO_IGUAL expresion PUNTO_COMA'''
    p[0] = Asignacion(destino=p[1], operador=p[2], valor=p[3],
                      linea=p[1].linea, columna=p[1].columna)


# if / else 
def p_if_stmt_sin_else(p):
    'if_stmt : IF expresion bloque'
    p[0] = If(condicion=p[2], bloque_entonces=p[3], bloque_sino=None, **pos(p, 1))


def p_if_stmt_con_else(p):
    'if_stmt : IF expresion bloque ELSE bloque'
    p[0] = If(condicion=p[2], bloque_entonces=p[3], bloque_sino=p[5], **pos(p, 1))


def p_if_stmt_else_if(p):
    'if_stmt : IF expresion bloque ELSE if_stmt'
    p[0] = If(condicion=p[2], bloque_entonces=p[3], bloque_sino=Bloque([p[5]]), **pos(p, 1))


# while 
def p_while_stmt(p):
    'while_stmt : WHILE expresion bloque'
    p[0] = While(condicion=p[2], bloque=p[3], **pos(p, 1))


# loop 
def p_loop_stmt_sin_etiqueta(p):
    'loop_stmt : LOOP bloque'
    p[0] = Loop(bloque=p[2], etiqueta=None, **pos(p, 1))


def p_loop_stmt_con_etiqueta(p):
    'loop_stmt : ETIQUETA DOS_PUNTOS LOOP bloque'
    p[0] = Loop(bloque=p[4], etiqueta=p[1], **pos(p, 1))


def p_match_stmt(p):
    'match_stmt : MATCH expresion LLAVE_IZQ lista_casos LLAVE_DER'
    p[0] = Match(expresion=p[2], casos=p[4], **pos(p, 1))


def p_match_stmt_caso_final(p):
    'match_stmt : MATCH expresion LLAVE_IZQ lista_casos caso_final LLAVE_DER'
    p[0] = Match(expresion=p[2], casos=p[4] + [p[5]], **pos(p, 1))


def p_match_stmt_solo_final(p):
    'match_stmt : MATCH expresion LLAVE_IZQ caso_final LLAVE_DER'
    p[0] = Match(expresion=p[2], casos=[p[4]], **pos(p, 1))


def p_lista_casos_uno(p):
    'lista_casos : caso'
    p[0] = [p[1]]


def p_lista_casos_varios(p):
    'lista_casos : lista_casos caso'
    p[0] = p[1] + [p[2]]


def p_caso(p):
    '''caso : caso_con_coma
            | caso_bloque'''
    p[0] = p[1]


# "patron => cuerpo ,"   (el cuerpo puede ser expresion o bloque)
def p_caso_con_coma(p):
    'caso_con_coma : patron FLECHA_MATCH bloque_o_expresion COMA'
    p[0] = CasoMatch(patron=p[1], bloque=p[3], linea=p[3].linea, columna=p[3].columna)


# ultimo caso sin coma:  "patron => expresion }"
def p_caso_final(p):
    'caso_final : patron FLECHA_MATCH expresion'
    p[0] = CasoMatch(patron=p[1], bloque=Bloque([p[3]], linea=p[3].linea, columna=p[3].columna),
                     linea=p[3].linea, columna=p[3].columna)


# "patron => { ... }"  sin coma (como en Rust)
def p_caso_bloque(p):
    'caso_bloque : patron FLECHA_MATCH bloque'
    p[0] = CasoMatch(patron=p[1], bloque=p[3], linea=p[3].linea, columna=p[3].columna)


def p_patron_expresion(p):
    'patron : expresion'
    p[0] = p[1]


def p_patron_comodin(p):
    'patron : COMODIN'
    p[0] = None

def p_bloque_o_expresion_bloque(p):
    'bloque_o_expresion : bloque'
    p[0] = p[1]


def p_bloque_o_expresion_expr(p):
    'bloque_o_expresion : expresion'
    p[0] = Bloque([p[1]], linea=p[1].linea, columna=p[1].columna)


# break / continue / return 
def p_break_sin_etiqueta(p):
    'break_stmt : BREAK PUNTO_COMA'
    p[0] = Break(etiqueta=None, **pos(p, 1))


def p_break_con_etiqueta(p):
    'break_stmt : BREAK ETIQUETA PUNTO_COMA'
    p[0] = Break(etiqueta=p[2], **pos(p, 1))


def p_continue_sin_etiqueta(p):
    'continue_stmt : CONTINUE PUNTO_COMA'
    p[0] = Continue(etiqueta=None, **pos(p, 1))


def p_continue_con_etiqueta(p):
    'continue_stmt : CONTINUE ETIQUETA PUNTO_COMA'
    p[0] = Continue(etiqueta=p[2], **pos(p, 1))


def p_return_sin_valor(p):
    'return_stmt : RETURN PUNTO_COMA'
    p[0] = Return(valor=None, **pos(p, 1))


def p_return_con_valor(p):
    'return_stmt : RETURN expresion PUNTO_COMA'
    p[0] = Return(valor=p[2], **pos(p, 1))




def p_lista_argumentos_uno(p):
    'lista_argumentos : expresion'
    p[0] = [p[1]]


def p_lista_argumentos_varios(p):
    'lista_argumentos : lista_argumentos COMA expresion'
    p[0] = p[1] + [p[3]]


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
    p[0] = OperacionBinaria(p[1], p[2], p[3], **pos(p, 2))


def p_expresion_menos_unario(p):
    'expresion : MENOS expresion %prec UMENOS'
    p[0] = OperacionUnaria('-', p[2], **pos(p, 1))

def p_expresion_llamada_funcion(p):
    'expresion : IDENTIFICADOR PAREN_IZQ lista_argumentos_opt PAREN_DER'
    p[0] = LlamadaFuncion(nombre=p[1], argumentos=p[3], **pos(p, 1))

def p_expresion_not(p):
    'expresion : NOT expresion'
    p[0] = OperacionUnaria('!', p[2], **pos(p, 1))


def p_expresion_agrupada(p):
    'expresion : PAREN_IZQ expresion PAREN_DER'
    p[0] = p[2]


def p_expresion_numero_entero(p):
    'expresion : NUMERO_ENTERO'
    p[0] = Literal(p[1], 'i32', **pos(p, 1))


def p_expresion_numero_decimal(p):
    'expresion : NUMERO_DECIMAL'
    p[0] = Literal(p[1], 'f64', **pos(p, 1))


def p_expresion_string(p):
    'expresion : STRING'
    p[0] = Literal(p[1], 'String', **pos(p, 1))


def p_expresion_char(p):
    'expresion : CHAR'
    p[0] = Literal(p[1], 'char', **pos(p, 1))


def p_expresion_true(p):
    'expresion : TRUE'
    p[0] = Literal(True, 'bool', **pos(p, 1))


def p_expresion_false(p):
    'expresion : FALSE'
    p[0] = Literal(False, 'bool', **pos(p, 1))


def p_expresion_identificador(p):
    'expresion : IDENTIFICADOR'
    p[0] = Identificador(p[1], **pos(p, 1))


# Arreglos y slices 
def p_expresion_arreglo(p):
    'expresion : CORCH_IZQ lista_argumentos_opt CORCH_DER'
    p[0] = Arreglo(elementos=p[2], **pos(p, 1))


def p_expresion_acceso_indice(p):
    'expresion : expresion CORCH_IZQ expresion CORCH_DER'
    p[0] = AccesoIndice(arreglo=p[1], indice=p[3],
                        linea=p[1].linea, columna=p[1].columna)



def p_expresion_slice(p):
    'expresion : AMPER expresion CORCH_IZQ expresion RANGO expresion CORCH_DER'
    p[0] = Slice(arreglo=p[2], inicio=p[4], fin=p[6], **pos(p, 1))



# String::from(...) 
def p_expresion_println(p):
    'expresion : IDENTIFICADOR NOT PAREN_IZQ lista_argumentos_opt PAREN_DER'
    if p[1] != 'println':
        agregar_error("Sintactico", f"Funcion embebida desconocida '{p[1]}!'", p.lineno(1))
    args = p[4]
    if args and isinstance(args[0], Literal) and args[0].tipo == 'String':
        p[0] = LlamadaPrintln(formato=args[0].valor, argumentos=args[1:], **pos(p, 1))
    else:
        p[0] = LlamadaPrintln(formato=None, argumentos=args, **pos(p, 1))


def p_expresion_metodo(p):
    'expresion : expresion PUNTO IDENTIFICADOR PAREN_IZQ lista_argumentos_opt PAREN_DER'
    p[0] = LlamadaMetodo(objeto=p[1], nombre=p[3], argumentos=p[5],
                         linea=p[1].linea, columna=p[1].columna)


def p_expresion_string_estatico(p):
    'expresion : TIPO_STRING DOBLE_DOS_PUNTOS IDENTIFICADOR PAREN_IZQ lista_argumentos_opt PAREN_DER'
    p[0] = LlamadaFuncion(nombre=f'String::{p[3]}', argumentos=p[5], **pos(p, 1))



def p_empty(p):
    'empty :'
    pass

# Manejo de errores sintácticos
SIMBOLOS = {'PUNTO_COMA': ';', 'PAREN_DER': ')', 'CORCH_DER': ']', 'LLAVE_DER': '}',
            'LLAVE_IZQ': '{', 'PAREN_IZQ': '(', 'COMA': ',', 'DOS_PUNTOS': ':', 'IGUAL': '='}
PRIORIDAD_ESPERADOS = ['PUNTO_COMA', 'PAREN_DER', 'CORCH_DER', 'LLAVE_DER']


def _fin_del_token_anterior(texto, lexpos):
    """(linea, columna) justo despues del ultimo caracter que no es espacio antes de lexpos."""
    pos = lexpos
    while pos > 0 and texto[pos - 1] in ' \t\r\n':
        pos -= 1
    linea = texto.count('\n', 0, pos) + 1
    return linea, encontrar_columna(texto, pos) if pos < len(texto) else pos - (texto.rfind('\n', 0, pos) + 1) + 1


def _esperados():
    """Simbolos que el parser habria aceptado en el estado donde fallo."""
    try:
        return set(parser.action[parser.statestack[-1]].keys())
    except Exception:
        return set()


def p_error(p):
    texto = lexer_actual().lexdata if p is None else p.lexer.lexdata
    esperados = _esperados()
    cerrador = next((t for t in PRIORIDAD_ESPERADOS if t in esperados), None)

    if p is None:                                       # fin de archivo
        linea, columna = _fin_del_token_anterior(texto, len(texto))
        if cerrador:
            agregar_error("Sintactico", f"Se esperaba '{SIMBOLOS[cerrador]}'.", linea, columna)
        else:
            agregar_error("Sintactico", "Fin de archivo inesperado.", linea, columna)
        return

    prev_linea, prev_col = _fin_del_token_anterior(texto, p.lexpos)
    en_otra_linea = prev_linea != p.lineno
    if cerrador and (en_otra_linea or cerrador == 'PUNTO_COMA'):
        # falta un ';' (o un cierre): se senala justo despues del ultimo token valido
        linea, columna = (prev_linea, prev_col) if en_otra_linea else (p.lineno, encontrar_columna(texto, p.lexpos))
        agregar_error("Sintactico", f"Se esperaba '{SIMBOLOS[cerrador]}'.", linea, columna)
    else:
        agregar_error("Sintactico", f"Error de sintaxis cerca de '{p.value}'",
                      p.lineno, encontrar_columna(texto, p.lexpos))


def lexer_actual():
    from compiler.lexer.lexer import lexer
    return lexer
parser = yacc.yacc()