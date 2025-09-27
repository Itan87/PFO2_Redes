# API REST básica con Flask, SQLite y autenticación HTTP Basic
# Implementa: Registro de usuarios con hash de contraseñas, Login con Basic Auth,
# y un endpoint protegido (/tareas).

from flask import Flask, request, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, base64

app = Flask(__name__)
DB = "pfo_tasks.db"  # Archivo de base de datos SQLite

# -----------------------
# Helpers de base de datos
# -----------------------
def get_db_conn():
    """Establece conexión con la base de datos SQLite."""
    # Desactivar el autocommit por defecto para mejor control de transacciones
    conn = sqlite3.connect(DB)
    # Habilitar el acceso por nombre de columna
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa la estructura de la base de datos (tablas users y tasks)."""
    conn = get_db_conn()
    cur = conn.cursor()
    # Tabla de Usuarios
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    );
    """)
    # Tabla de Tareas (opcional pero útil para un gestor de tareas)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    """)
    conn.commit()
    conn.close()

# -----------------------
# Autenticación básica (Basic Auth)
# -----------------------
def get_auth_credentials():
    """Obtiene usuario y contraseña del header Authorization (Basic)."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Basic "):
        return None, None
    encoded = auth_header.split(" ", 1)[1]
    try:
        # Decodifica Base64 y separa 'usuario:contraseña'
        decoded = base64.b64decode(encoded).decode("utf-8")
        usuario, contraseña = decoded.split(":", 1)
        return usuario, contraseña
    except Exception:
        # Error al decodificar o en el formato
        return None, None

def require_auth():
    """Genera una respuesta 401 que le indica al cliente que debe autenticarse."""
    resp = make_response(jsonify({"error": "Autenticación requerida para acceder a este recurso."}), 401)
    # Importante: Este header le indica al navegador/cliente que use Basic Auth
    resp.headers["WWW-Authenticate"] = 'Basic realm="Acceso a tareas"'
    return resp

def authenticate():
    """Verifica las credenciales en la base de datos. Retorna el user_id si es exitoso."""
    usuario, contraseña = get_auth_credentials()
    if not usuario or not contraseña:
        return None
    
    conn = get_db_conn()
    cur = conn.cursor()
    # Buscar el usuario por nombre
    cur.execute("SELECT id, password_hash FROM users WHERE usuario = ?", (usuario,))
    row = cur.fetchone()
    conn.close()

    if row and check_password_hash(row['password_hash'], contraseña):
        return row['id']  # Autenticación exitosa, devuelve el ID del usuario
    return None # Autenticación fallida

# -----------------------
# Endpoints
# -----------------------

@app.route("/", methods=["GET"])
def index():
    """Ruta raíz de la API para confirmar que está activa."""
    return jsonify({
        "status": "API de Gestión de Tareas activa",
        "endpoints": [
            "POST /registro",
            "GET /login (con Basic Auth)",
            "GET /tareas (con Basic Auth)"
        ]
    })


@app.route("/registro", methods=["POST"])
def registro():
    """Endpoint para registrar un nuevo usuario."""
    try:
        data = request.get_json(force=True)
        usuario = data.get("usuario")
        contraseña = data.get("contraseña")
    except:
        return jsonify({"error": "Formato JSON inválido"}), 400

    if not usuario or not contraseña:
        return jsonify({"error": "Los campos 'usuario' y 'contraseña' son requeridos"}), 400


# 1. Hashear la contraseña
    pwd_hash = generate_password_hash(contraseña)

    try:
        # 2. Almacenar el usuario en SQLite
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (usuario, password_hash) VALUES (?, ?)", (usuario, pwd_hash))
        conn.commit()
        conn.close()
        return jsonify({"message": f"Usuario '{usuario}' registrado correctamente"}), 201
    except sqlite3.IntegrityError:
        # Error al insertar (UNIQUE constraint), el usuario ya existe
        return jsonify({"error": f"El usuario '{usuario}' ya existe"}), 409
    except Exception as e:
        # Manejar otros errores de DB
        print(f"Error de base de datos en registro: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500


@app.route("/login", methods=["GET"])
def login():
    """Verifica credenciales básicas. No devuelve un token, solo confirma el acceso."""
    user_id = authenticate()
    if user_id:
        return jsonify({"message": "Login correcto. Credenciales verificadas."})
    
    # Si la autenticación falla, se solicita nuevamente
    return require_auth()


@app.route("/tareas", methods=["GET"])
def tareas():
    """Muestra un HTML de bienvenida, protegido por autenticación básica."""
    user_id = authenticate()

    if not user_id:
        # Si no está autenticado, solicita credenciales
        return require_auth()
    
    # Si está autenticado, sirve la página HTML
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="utf-8">
      <title>Gestor de Tareas PFO 2</title>
      <style>
        body {{ font-family: sans-serif; background-color: #f4f7f6; color: #333; text-align: center; padding-top: 50px; }}
        h1 {{ color: #2c3e50; }}
        .container {{ background: #fff; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); display: inline-block; padding: 40px; }}
        p {{ color: #7f8c8d; }}
      </style>
    </head>
    <body>
      <div class="container">
        <h1>Bienvenido al Gestor de Tareas</h1>
        <p>¡Has iniciado sesión correctamente! (User ID: {user_id})</p>
        <p>Este es el HTML protegido solicitado en el punto 3 de la consigna.</p>
        <p>Utiliza el cliente de consola para probar todos los endpoints.</p>
      </div>
    </body>
    </html>
    """
    resp = make_response(html)
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    return resp

# -----------------------
# Inicio de la app
# -----------------------
if __name__ == "__main__":
    init_db()
    print("--- Inicialización de Base de Datos y Servidor ---")
    print(f"Base de datos: {DB}")
    print("Servidor iniciado en http://127.0.0.1:5000")
    print("-------------------------------------------------")
    app.run(host="127.0.0.1", port=5000, debug=True)