"""
Tabla de simbolos con soporte de ambitos (scopes) anidados.
Cada scope es un diccionario {nombre: info_simbolo}.
"""

class Simbolo:
    def __init__(self, nombre, tipo, mutable=False, categoria="Variable", linea=0, valor=None):
        self.nombre = nombre
        self.tipo = tipo
        self.mutable = mutable
        self.categoria = categoria  # 'Variable', 'Funcion', 'Parametro'
        self.linea = linea
        self.valor = valor
        self.ambito = "Global"

    def __repr__(self):
        return f"Simbolo({self.nombre}: {self.tipo}, mut={self.mutable})"


class TablaSimbolos:
    def __init__(self):
        self.scopes = [{}]
        self.simbolos_para_reporte = []
        self.ambito_actual = "Global"

    def entrar_scope(self):
        self.scopes.append({})

    def salir_scope(self):
        self.scopes.pop()

    def declarar(self, nombre, simbolo):
        simbolo.ambito = self.ambito_actual
        self.scopes[-1][nombre] = simbolo
        self.simbolos_para_reporte.append(simbolo)

    def buscar(self, nombre):
        for scope in reversed(self.scopes):
            if nombre in scope:
                return scope[nombre]
        return None

    def existe_en_scope_actual(self, nombre):
        return nombre in self.scopes[-1]