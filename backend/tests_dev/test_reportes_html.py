import os
from compiler.parser.parser import parser
from compiler.semantic.analizador import AnalizadorSemantico
from compiler.errors import limpiar_errores, obtener_errores
from compiler.reportes import reporte_errores_html, reporte_simbolos_html

codigo = '''
fn sumar(a: i32, b: i32) -> i32 {
    return a + b;
}

fn main() {
    let contador: i32 = 10;
    let nombre = String::from("Ana");
    let mut total: f64;
    let edad = 20;
    edad = 21;
    let r = sumar(contador, 5);
    println!("{}", r);
}
'''

limpiar_errores()
ast = parser.parse(codigo)
analizador = AnalizadorSemantico()
analizador.analizar(ast)

os.makedirs("reportes", exist_ok=True)

with open("reportes/errores.html", "w", encoding="utf-8") as f:
    f.write(reporte_errores_html(obtener_errores()))

with open("reportes/simbolos.html", "w", encoding="utf-8") as f:
    f.write(reporte_simbolos_html(analizador.tabla.simbolos_para_reporte))

print("Reportes generados en la carpeta reportes/")
