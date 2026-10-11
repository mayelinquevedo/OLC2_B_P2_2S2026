import html

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
