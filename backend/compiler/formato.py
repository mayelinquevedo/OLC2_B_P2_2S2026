"""Interpretacion de la cadena de formato de println!."""

def partir_formato(formato):
    """Devuelve una lista de piezas:  ("txt", texto)  o  ("arg", es_debug).
    Lanza ValueError si hay una llave sin pareja o un marcador desconocido."""
    piezas = []
    texto = []
    i, n = 0, len(formato)
    while i < n:
        c = formato[i]
        if c == "{":
            if i + 1 < n and formato[i + 1] == "{":
                texto.append("{")
                i += 2
                continue
            fin = formato.find("}", i)
            if fin == -1:
                raise ValueError("falta '}' para cerrar un marcador")
            interior = formato[i + 1:fin]
            if interior not in ("", ":?"):
                raise ValueError(f"marcador no soportado '{{{interior}}}'")
            if texto:
                piezas.append(("txt", "".join(texto)))
                texto = []
            piezas.append(("arg", interior == ":?"))
            i = fin + 1
        elif c == "}":
            if i + 1 < n and formato[i + 1] == "}":
                texto.append("}")
                i += 2
                continue
            raise ValueError("'}' sin su '{' correspondiente (use '}}' para una llave literal)")
        else:
            texto.append(c)
            i += 1
    if texto:
        piezas.append(("txt", "".join(texto)))
    return piezas


def contar_marcadores(piezas):
    return sum(1 for tipo, _ in piezas if tipo == "arg")