"""Corre los programas de tests/ejemplos y compara con su archivo .esperado.

Uso (desde backend/):
    python3 -m tests_dev.correr_ejemplos            # compara
    python3 -m tests_dev.correr_ejemplos --generar  # (re)escribe los .esperado con la salida actual

Cada .esperado contiene la salida del programa, o las lineas
"[Tipo] Linea L, Columna C: descripcion" si el programa debe producir errores.
"""
import glob
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
from compiler.pipeline import compilar                      # noqa: E402

CARPETA = os.path.join(os.path.dirname(RAIZ), "tests", "ejemplos")


def resultado(codigo):
    r = compilar(codigo)
    if r["errores"]:
        return "\n".join(f"[{e['tipo']}] Linea {e['linea']}, Columna {e['columna']}: {e['descripcion']}"
                         for e in r["errores"]) + "\n"
    return r["salida"]


def main():
    generar = "--generar" in sys.argv
    fallos = 0
    archivos = sorted(glob.glob(os.path.join(CARPETA, "*.ox")))
    for ruta in archivos:
        nombre = os.path.basename(ruta)
        obtenido = resultado(open(ruta, encoding="utf-8").read())
        esperado_ruta = ruta[:-3] + ".esperado"
        if generar:
            open(esperado_ruta, "w", encoding="utf-8").write(obtenido)
            print(f"  generado {nombre}")
            continue
        esperado = open(esperado_ruta, encoding="utf-8").read() if os.path.exists(esperado_ruta) else None
        if obtenido == esperado:
            print(f"  OK     {nombre}")
        else:
            fallos += 1
            print(f"  FALLA  {nombre}")
    if not generar:
        print(f"\n{len(archivos) - fallos} de {len(archivos)} ejemplos correctos.")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
