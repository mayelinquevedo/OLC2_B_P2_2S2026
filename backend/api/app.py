"""API REST de OxigenNative (Flask).

desde carpeta backend/:   python -m api.app
"""
import os

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from compiler.pipeline import compilar, CARPETA_REPORTES

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CARPETA_FRONTEND = os.path.join(RAIZ, "frontend")
REPORTES_PERMITIDOS = {"errores.html", "simbolos.html", "ast.svg", "ast.dot"}
MAX_CODIGO = 200_000

app = Flask(__name__, static_folder=None)
app.json.ensure_ascii = False
CORS(app)


@app.post("/api/compilar")
def api_compilar():
    datos = request.get_json(silent=True) or {}
    codigo = datos.get("codigo")
    if not isinstance(codigo, str):
        return jsonify({"ok": False, "fase": "solicitud",
                        "mensaje": "La solicitud debe ser un JSON con el campo 'codigo' (texto)."}), 400
    if len(codigo) > MAX_CODIGO:
        return jsonify({"ok": False, "fase": "solicitud",
                        "mensaje": f"El codigo excede {MAX_CODIGO} caracteres."}), 413
    return jsonify(compilar(codigo))


@app.get("/api/reportes/<nombre>")
def api_reporte(nombre):
    """Ultimo reporte generado: errores.html, simbolos.html, ast.svg o ast.dot."""
    if nombre not in REPORTES_PERMITIDOS:
        return jsonify({"mensaje": "Reporte desconocido."}), 404
    if not os.path.exists(os.path.join(CARPETA_REPORTES, nombre)):
        return jsonify({"mensaje": "Ese reporte aun no existe: compile un programa primero."}), 404
    descargar = request.args.get("descargar") == "1"
    return send_from_directory(CARPETA_REPORTES, nombre, as_attachment=descargar)


@app.get("/")
def indice():
    return send_from_directory(CARPETA_FRONTEND, "index.html")


@app.get("/<path:ruta>")
def estaticos(ruta):
    return send_from_directory(CARPETA_FRONTEND, ruta)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)