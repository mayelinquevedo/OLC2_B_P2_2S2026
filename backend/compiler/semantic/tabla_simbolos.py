"""
Tabla de simbolos con soporte de ambitos (scopes) anidados.
Cada scope es un diccionario {nombre: info_simbolo}.
La busqueda de un simbolo recorre desde el scope mas interno
hacia externos 
"""

class Simbolo:
    def __init__(self, nombre, tipo, mutable=False, categoria="Variable", linea=0, valor=None):
        self.nombre = nombre
        self.tipo = tipo
        self.mutable = mutable
        self.categoria = categoria  # 'Variable', 'Funcion', 'Parametro'
        self.linea = linea
        self.valor = valor  #  para el reporte de tabla de simbolos

    def __repr__(self):
        return f"Simbolo({self.nombre}: {self.tipo}, mut={self.mutable})"


class TablaSimbolos:
    def __init__(self):
        self.scopes = [{}]
        self.simbolos_para_reporte = []  

    def entrar_scope(self):
        self.scopes.append({})

    def salir_scope(self):
        self.scopes.pop()

    def declarar(self, nombre, simbolo):
        """Declara un simbolo en el scope actual (el mas interno)."""
        self.scopes[-1][nombre] = simbolo
        self.simbolos_para_reporte.append(simbolo)

    def buscar(self, nombre):
        """Busca un simbolo desde el scope mas interno hacia afuera."""
        for scope in reversed(self.scopes):
            if nombre in scope:
                return scope[nombre]
        return None

    def existe_en_scope_actual(self, nombre):
        return nombre in self.scopes[-1]