"""
Acumula errores léxicos, sintácticos y semánticos sin detener
"""

errores = []

def agregar_error(tipo: str, descripcion: str, linea: int, columna: int = 0):
    errores.append({
        "tipo": tipo,
        "descripcion": descripcion,
        "linea": linea,
        "columna": columna
    })

def encontrar_columna(texto: str, lexpos: int) -> int:
    inicio_linea = texto.rfind('\n', 0, lexpos) + 1
    return (lexpos - inicio_linea) + 1

def hay_errores() -> bool:
    return len(errores) > 0

def limpiar_errores():
    global errores
    errores = []

def imprimir_reporte():
    for e in errores:
        print(f"[Error {e['tipo']}] Línea {e['linea']}, Columna {e['columna']}")
        print(e['descripcion'])
        print()