import os
import subprocess
import time


def _correr(comando, **opciones):
    return subprocess.run(comando, capture_output=True, text=True, errors="replace", **opciones)


def ejecutar(asm, carpeta="salida", limite_segundos=10):
    os.makedirs(carpeta, exist_ok=True)
    ruta_s = os.path.join(carpeta, "programa.s")
    ruta_o = os.path.join(carpeta, "programa.o")
    ruta_exe = os.path.join(carpeta, "programa")

    with open(ruta_s, "w", encoding="utf-8") as f:
        f.write(asm)

    r = _correr(["aarch64-linux-gnu-as", ruta_s, "-o", ruta_o])
    if r.returncode != 0:
        return {"ok": False, "fase": "ensamblado", "error": r.stderr}

    r = _correr(["aarch64-linux-gnu-ld", ruta_o, "-o", ruta_exe])
    if r.returncode != 0:
        return {"ok": False, "fase": "enlace", "error": r.stderr}

    inicio = time.time()
    try:
        r = _correr(["qemu-aarch64", ruta_exe], timeout=limite_segundos)
    except subprocess.TimeoutExpired:
        return {"ok": False, "fase": "ejecucion",
                "error": f"El programa excedio {limite_segundos} segundos."}
    tiempo = time.time() - inicio

    return {"ok": True, "salida": r.stdout, "codigo": r.returncode,
            "tiempo": tiempo, "stderr": r.stderr}
