import os
from compiler.pipeline import compilar, CARPETA_REPORTES


def chk(nombre, cond, detalle=""):
    print(("OK     " if cond else "FALLA  ") + nombre, "" if cond else f"-> {detalle}")


def src(*lineas):
    return "\n".join(lineas) + "\n"


valido = src("fn main() {", "    let x: i32 = 10;", '    println!("x = {}", x);', "}")
r = compilar(valido)
chk("programa valido", r["ok"] and r["salida"] == "x = 10\n" and r["codigo_salida"] == 0, r["mensaje"])
chk("devuelve el ensamblador", bool(r["asm"]) and "fn_main" in r["asm"])
chk("devuelve la tabla de simbolos",
    any(s["nombre"] == "x" and s["ambito"] == "main" and s["valor"] == "10" for s in r["simbolos"]), r["simbolos"])
chk("devuelve el AST en SVG", bool(r["ast_svg"]) and r["ast_svg"].startswith("<svg"))
chk("escribe los reportes", all(os.path.exists(os.path.join(CARPETA_REPORTES, n))
                                for n in ("errores.html", "simbolos.html", "ast.dot", "ast.svg")))

lexico = src("fn main() {", "    let total = @100;", "}")
for vez in (1, 2):
    r = compilar(lexico)
    chk(f"error lexico en la linea 2 (intento {vez})",
        (not r["ok"]) and any(e["tipo"] == "Lexico" and e["linea"] == 2 for e in r["errores"]), r["errores"])

sintactico = src("fn main() {", "    let x: i32 = 10", '    println!("{}", x);', "}")
r = compilar(sintactico)
chk("error sintactico", (not r["ok"]) and any(e["tipo"] == "Sintactico" for e in r["errores"]), r["errores"])

semantico = src("fn main() {", "    let edad = 20;", "    edad = 21;", "}")
r = compilar(semantico)
chk("error semantico (linea 3, columna 5)",
    (not r["ok"]) and r["errores"] and r["errores"][0]["tipo"] == "Semantico"
    and r["errores"][0]["linea"] == 3 and r["errores"][0]["columna"] == 5, r["errores"])
chk("con error semantico igual hay AST", bool(r["ast_svg"]))

no_soportado = src("fn main() {", "    let numeros = [1, 2, 3];", "    let parte = &numeros[0..2];", "}")
r = compilar(no_soportado)
chk("construccion que el generador aun no soporta",
    (not r["ok"]) and r["fase"] == "generacion" and any(e["tipo"] == "Generacion" for e in r["errores"]), r)

en_ejecucion = src("fn main() {", "    let mut d = 0;", '    println!("{}", 10 / d);', "}")
r = compilar(en_ejecucion)
chk("error de ejecucion (division entre cero)",
    r["ok"] and r["codigo_salida"] == 1 and "división entre cero" in r["salida"], r["salida"])

r = compilar(valido)
chk("despues de varios errores todo sigue funcionando", r["ok"] and r["salida"] == "x = 10\n", r["mensaje"])