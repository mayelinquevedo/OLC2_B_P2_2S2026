import ply.lex as lex
from compiler.errors import agregar_error, encontrar_columna

# Palabras reservadas del lenguaje OxigenNative 
reservadas = {
    'let': 'LET',
    'mut': 'MUT',
    'fn': 'FN',
    'if': 'IF',
    'else': 'ELSE',
    'while': 'WHILE',
    'loop': 'LOOP',
    'match': 'MATCH',
    'return': 'RETURN',
    'break': 'BREAK',
    'continue': 'CONTINUE',
    'true': 'TRUE',
    'false': 'FALSE',

    # tipos del lenguaje
    'i32': 'TIPO_I32',
    'f64': 'TIPO_F64',
    'bool': 'TIPO_BOOL',
    'char': 'TIPO_CHAR',
    'String': 'TIPO_STRING',
}



# Lista de tokens
tokens = [
    'IDENTIFICADOR',
    'NUMERO_ENTERO',
    'NUMERO_DECIMAL',
    'STRING', 'CHAR', 'ETIQUETA',
    'MAS', 'MENOS',
    'MULT', 'DIV', 'MODULO',
    'IGUAL',
    'MAYORQUE', 'MENORQUE',
    'IGUAL_IGUAL', 'DIFERENTE',
    'MAYOR_IGUAL', 'MENOR_IGUAL',
    'AND', 'OR', 'NOT', 'AMPER',
    'MAS_IGUAL', 'MENOS_IGUAL',
    'MULT_IGUAL', 'DIV_IGUAL', 'MODULO_IGUAL',
    'RANGO',
    'DOBLE_DOS_PUNTOS',
    'FLECHA', 'FLECHA_MATCH',
    'LLAVE_IZQ', 'LLAVE_DER',
    'PAREN_IZQ', 'PAREN_DER',
    'CORCH_IZQ', 'CORCH_DER',
    'DOS_PUNTOS', 'PUNTO_COMA',
    'COMA', 'PUNTO',

] + list(reservadas.values())


# Identificadores
def t_IDENTIFICADOR(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reservadas.get(t.value, 'IDENTIFICADOR')
    return t

# Tokens simples (símbolos y operadores de un solo carácter)
t_MAS = r'\+'
t_MENOS = r'-'
t_MULT = r'\*'
t_DIV = r'/'
t_MODULO = r'%'

t_LLAVE_IZQ = r'\{'
t_LLAVE_DER = r'\}'
t_PAREN_IZQ = r'\('
t_PAREN_DER = r'\)'
t_CORCH_IZQ = r'\['
t_CORCH_DER = r'\]'

t_DOS_PUNTOS = r':'
t_PUNTO_COMA = r';'
t_COMA = r','
t_PUNTO = r'\.'


# Números enteros y decimales
def t_NUMERO_DECIMAL(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t

def t_NUMERO_ENTERO(t):
    r'\d+'
    t.value = int(t.value)
    return t


# Strings 
def t_STRING(t):
    r'"([^"\\]|\\.)*"'
    contenido = t.value[1:-1]
    contenido = contenido.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
    t.value = contenido
    return t

# Chars (un solo carácter entre comillas simples)
def t_CHAR(t):
    r"'([^'\\]|\\.)'"
    t.value = t.value[1:-1]
    return t


# Etiquetas de loop 
def t_ETIQUETA(t):
    r"'[a-zA-Z_][a-zA-Z0-9_]*"
    t.value = t.value[1:]  # quitar la comilla simple al inicio
    return t


# Operadores compuestos 
def t_IGUAL_IGUAL(t):
    r'=='
    return t

def t_DIFERENTE(t):
    r'!='
    return t

def t_DOBLE_DOS_PUNTOS(t):
    r'::'
    return t

def t_FLECHA(t):
    r'->'
    return t

def t_FLECHA_MATCH(t):
    r'=>'
    return t

def t_MAYOR_IGUAL(t):
    r'>='
    return t

def t_MENOR_IGUAL(t):
    r'<='
    return t

def t_AND(t):
    r'&&'
    return t

def t_OR(t):
    r'\|\|'
    return t

def t_MAS_IGUAL(t):
    r'\+='
    return t

def t_MENOS_IGUAL(t):
    r'-='
    return t

def t_MULT_IGUAL(t):
    r'\*='
    return t

def t_DIV_IGUAL(t):
    r'/='
    return t

def t_MODULO_IGUAL(t):
    r'%='
    return t

def t_RANGO(t):
    r'\.\.'
    return t


t_IGUAL = r'='
t_MAYORQUE = r'>'
t_MENORQUE = r'<'
t_NOT = r'!'
t_AMPER = r'&'


# Comentarios 
def t_COMENTARIO_LINEA(t):
    r'//[^\n]*'
    pass

def t_COMENTARIO_BLOQUE(t):
    r'/\*(.|\n)*?\*/'
    t.lexer.lineno += t.value.count('\n')
    pass


def t_COMENTARIO_BLOQUE_SIN_CERRAR(t):
    r'/\*(.|\n)*'
    agregar_error("Lexico", "Comentario de bloque sin cerrar (falta '*/')", t.lineno,
                  encontrar_columna(t.lexer.lexdata, t.lexpos))
    t.lexer.lineno += t.value.count('\n')
    pass


# Caracteres ignorados
t_ignore = ' \t'


# Seguimiento de línea
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


# Manejo de errores léxicos 
def t_error(t):
    columna = encontrar_columna(t.lexer.lexdata, t.lexpos)
    agregar_error("Lexico", f"Caracter no reconocido '{t.value[0]}'", t.lineno, columna)
    t.lexer.skip(1)

lexer = lex.lex()