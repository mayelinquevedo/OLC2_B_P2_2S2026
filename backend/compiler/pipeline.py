"""Orquesta todo el compilador: analisis lexico/sintactico -> semantico -> ARM64 -> QEMU.
"""
import os
import shutil
import tempfile
import threading

from compiler.lexer.lexer import lexer
from compiler.parser.parser import parser
from compiler.semantic.analizador import AnalizadorSemantico
from compiler.codegen.generador import GeneradorARM64
from compiler.errors import limpiar_errores, obtener_errores
from compiler import reportes
from runtime.ejecutor import ejecutar

CARPETA_REPORTES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reportes")
LIMITE_SEGUNDOS = 10
LIMITE_SALIDA = 100_000      # caracteres de salida que se devuelven al cliente
_candado = threading.Lock()


def _valor_texto(v):
    if v is None:
        return "—"
    if isinstance(v, bool):
        return str(v).lower()
    if isinstance(v, str):
        return f'"{v}"'
    return str(v)


def _simbolo_a_dict(s):
    return {"nombre": s.nombre, "categoria": s.categoria, "tipo": s.tipo,
            "ambito": s.ambito, "linea": s.linea, "valor": _valor_texto(s.valor)}


def _escribir_reportes(r, errores, simbolos, ast):
    """Genera los reportes HTML y el AST (DOT + SVG) en CARPETA_REPORTES."""
    os.makedirs(CARPETA_REPORTES, exist_ok=True)
    with open(os.path.join(CARPETA_REPORTES, "errores.html"), "w", encoding="utf-8") as f:
        f.write(reportes.reporte_errores_html(errores))
    with open(os.path.join(CARPETA_REPORTES, "simbolos.html"), "w", encoding="utf-8") as f:
        f.write(reportes.reporte_simbolos_html(simbolos))
    ruta_dot = os.path.join(CARPETA_REPORTES, "ast.dot")
    ruta_svg = os.path.join(CARPETA_REPORTES, "ast.svg")
    if ast is None:
        for ruta in (ruta_dot, ruta_svg):       # no dejar un AST de una compilacion anterior
            if os.path.exists(ruta):
                os.remove(ruta)
        return
    try:
        reportes.guardar_ast(ast, CARPETA_REPORTES)
        with open(ruta_svg, encoding="utf-8") as f:
            svg = f.read()
        r["ast_svg"] = svg[svg.index("<svg"):]   # sin el prologo XML, para incrustarlo en la pagina
    except Exception:
        r["ast_svg"] = None


def compilar(codigo):
    """Compila y ejecuta 'codigo'. Devuelve un diccionario listo para convertir a JSON."""
    with _candado:
        return _compilar(codigo)


def _compilar(codigo):
    r = {"ok": False, "fase": "analisis", "mensaje": "", "errores": [], "simbolos": [],
         "ast_svg": None, "asm": None, "salida": "", "codigo_salida": None, "tiempo": None}

    # ---- analisis lexico, sintactico y semantico ----
    limpiar_errores()
    lexer.lineno = 1
    ast = None
    simbolos = []
    interno = None
    try:
        ast = parser.parse(codigo, lexer=lexer)
        if ast is not None:
            analizador = AnalizadorSemantico()
            analizador.analizar(ast)
            simbolos = analizador.tabla.simbolos_para_reporte
    except Exception as e:            # un fallo interno no debe tumbar el servidor
        interno = e
    errores = list(obtener_errores())
    if interno is not None:
        errores.append({"tipo": "Interno", "linea": 0, "columna": 0,
                        "descripcion": f"Error interno del compilador: {type(interno).__name__}: {interno}"})
    lineas = codigo.split("\n")
    for e in errores:           # fragmento del codigo fuente donde se detecto el error
        e["fragmento"] = lineas[e["linea"] - 1].strip() if 0 < e["linea"] <= len(lineas) else ""
    r["errores"] = errores
    r["simbolos"] = [_simbolo_a_dict(s) for s in simbolos]
    _escribir_reportes(r, errores, simbolos, ast)

    if errores:
        r["mensaje"] = f"Se encontraron {len(errores)} error(es)"
        return r
    if ast is None:
        r["mensaje"] = "No se pudo construir el arbol de sintaxis"
        return r

    # ---- generacion de codigo ARM64 ----
    r["fase"] = "generacion"
    try:
        asm = GeneradorARM64().generar(ast)
    except NotImplementedError as e: 
        r["mensaje"] = str(e)
        r["errores"].append({"tipo": "Generacion", "descripcion": str(e), "linea": 0, "columna": 0})
        return r
    except Exception as e:
        r["mensaje"] = f"Error interno del generador: {type(e).__name__}: {e}"
        r["errores"].append({"tipo": "Interno", "descripcion": r["mensaje"], "linea": 0, "columna": 0})
        return r
    r["asm"] = asm

    # ---- ensamblado, enlace y ejecucion con QEMU  ----
    carpeta = tempfile.mkdtemp(prefix="oxigen_")
    try:
        res = ejecutar(asm, carpeta=carpeta, limite_segundos=LIMITE_SEGUNDOS)
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)

    if not res["ok"]:
        r["fase"] = res["fase"]
        r["mensaje"] = res["error"]
        return r
    salida = res["salida"]
    if len(salida) > LIMITE_SALIDA:
        salida = salida[:LIMITE_SALIDA] + "\n... (salida truncada)"
    r.update(ok=True, fase="ejecucion", mensaje="Compilación exitosa", salida=salida,
             codigo_salida=res["codigo"], tiempo=res["tiempo"])
    return r