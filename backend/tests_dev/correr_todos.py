
import importlib.util
import subprocess
import sys

PRUEBAS = [
    "test_codegen_enteros",
    "test_codegen_control",
    "test_codegen_funciones",
    "test_codegen_arreglos",
    "test_codegen_tipos",
    "test_codegen_strings",
    "test_codegen_errores_ejecucion",
    "test_pipeline",
]

MARCAS_DE_FALLO = ("NO COINCIDE", "FALLA", "Fallo en", "Traceback", "errores de compilacion", "[Error ")


def evaluar(salida, codigo):
    """Devuelve (paso, cuantas_verificaciones_ok)."""
    lineas = salida.splitlines()
    ok = sum(1 for l in lineas if "COINCIDE" in l and "NO COINCIDE" not in l or l.startswith("OK "))
    fallo = codigo != 0 or any(m in l for l in lineas for m in MARCAS_DE_FALLO)
    return (not fallo and ok > 0), ok


def main():
    resultados = []
    omitidas = []
    for nombre in PRUEBAS:
        if importlib.util.find_spec(f"tests_dev.{nombre}") is None:
            omitidas.append(nombre)          # esa prueba todavia no existe en el repo
            continue
        p = subprocess.run([sys.executable, "-m", f"tests_dev.{nombre}"],
                           capture_output=True, text=True, errors="replace")
        salida = p.stdout + p.stderr
        paso, ok = evaluar(salida, p.returncode)
        resultados.append((nombre, paso, ok, salida))
    print()
    for nombre, paso, ok, _ in resultados:
        print(f"  {'OK   ' if paso else 'FALLA'}  {nombre:<34} ({ok} verificaciones)")
    fallidas = [r for r in resultados if not r[1]]
    for nombre, _, _, salida in fallidas:
        print(f"\n===== {nombre}: ultimas lineas de su salida =====")
        print("\n".join(salida.splitlines()[-25:]))
    for nombre in omitidas:
        print(f"  ----   {nombre:<34} (omitida: el archivo aun no existe)")
    print(f"\n{len(resultados) - len(fallidas)} de {len(resultados)} pruebas pasaron.")
    return 1 if fallidas else 0


if __name__ == "__main__":
    sys.exit(main())
