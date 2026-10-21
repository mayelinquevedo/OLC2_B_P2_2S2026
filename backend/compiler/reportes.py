import html
import os
import subprocess
from compiler.ast.nodos import Nodo

ESTILO = """<style>
body{font-family:Arial,sans-serif;margin:24px}
table{border-collapse:collapse;width:100%}
th{background:#4a86e8;color:#fff;padding:8px;text-align:left}
td{border:1px solid #999;padding:8px}
</style>"""


def _pagina(titulo, encabezados, filas):
    cab = "".join(f"<th>{html.escape(h)}</th>" for h in encabezados)
    cuerpo = ""
    for fila in filas:
        celdas = "".join(f"<td>{html.escape(str(c))}</td>" for c in fila)
        cuerpo += f"<tr>{celdas}</tr>\n"
    return (f"<html><head><meta charset='utf-8'><title>{titulo}</title>{ESTILO}</head>"
            f"<body><h2>{titulo}</h2><table><tr>{cab}</tr>{cuerpo}</table></body></html>")


def _mostrar_valor(v):
    if v is None:
        return "—"
    if isinstance(v, bool):
        return str(v).lower()
    if isinstance(v, str):
        return f'"{v}"'
    return v


def reporte_errores_html(errores):
    filas = [[i + 1, e["tipo"], e["descripcion"], e["linea"], e["columna"]]
             for i, e in enumerate(errores)]
    return _pagina("Reporte de errores", ["No", "Tipo", "Descripción", "Línea", "Columna"], filas)


def reporte_simbolos_html(simbolos):
    filas = [[i + 1, s.nombre, s.categoria, s.tipo, s.ambito, s.linea, _mostrar_valor(s.valor)]
             for i, s in enumerate(simbolos)]
    return _pagina("Reporte de tabla de símbolos",
                   ["No.", "Identificador", "Categoría", "Tipo", "Ámbito", "Línea", "Valor"], filas)


def _esc(texto):
    return str(texto).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def ast_a_dot(raiz):
    lineas = ["digraph AST {", '  node [shape=box, fontname="Times"];']
    contador = [0]

    def visitar(nodo):
        contador[0] += 1
        mi_id = f"n{contador[0]}"
        etiqueta = type(nodo).__name__
        hijos = []
        for nombre, valor in vars(nodo).items():
            if nombre in ("linea", "columna", "tipo_resultado") or valor is None:
                continue
            if isinstance(valor, Nodo):
                hijos.append(valor)
            elif isinstance(valor, list):
                hijos.extend(v for v in valor if isinstance(v, Nodo))
            else:
                etiqueta += f"\n{nombre}: {valor}"
        lineas.append(f'  {mi_id} [label="{_esc(etiqueta)}"];')
        for h in hijos:
            hijo_id = visitar(h)
            lineas.append(f"  {mi_id} -> {hijo_id};")
        return mi_id

    visitar(raiz)
    lineas.append("}")
    return "\n".join(lineas)


def guardar_ast(ast, carpeta="reportes"):
    os.makedirs(carpeta, exist_ok=True)
    ruta_dot = os.path.join(carpeta, "ast.dot")
    ruta_svg = os.path.join(carpeta, "ast.svg")
    with open(ruta_dot, "w", encoding="utf-8") as f:
        f.write(ast_a_dot(ast))
    subprocess.run(["dot", "-Tsvg", ruta_dot, "-o", ruta_svg], check=True)
    return ruta_dot, ruta_svg
