from compiler.parser.parser import parser
from compiler.errors import limpiar_errores
from compiler.reportes import guardar_ast

codigo = '''
fn main() {
    let x = 10;
    println!("{}", x);
}
'''

limpiar_errores()
ast = parser.parse(codigo)
dot, svg = guardar_ast(ast)
print("Generado:", dot)
print("Generado:", svg)
