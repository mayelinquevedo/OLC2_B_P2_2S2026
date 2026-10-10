from compiler.semantic.tabla_simbolos import TablaSimbolos, Simbolo

tabla = TablaSimbolos()


tabla.declarar("x", Simbolo("x", "i32", mutable=False, linea=1))
print("x en global:", tabla.buscar("x"))


tabla.entrar_scope()
tabla.declarar("y", Simbolo("y", "f64", mutable=True, linea=2))
print("y en scope interno:", tabla.buscar("y"))
print("x sigue visible desde adentro:", tabla.buscar("x"))

tabla.salir_scope()
print("y despues de salir del scope (debe ser None):", tabla.buscar("y"))
print("x sigue existiendo:", tabla.buscar("x"))


tabla.declarar("x", Simbolo("x", "f64", mutable=False, linea=5))
print("x despues de shadowing:", tabla.buscar("x"))