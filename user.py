import hashlib
import json
import uuid
from pathlib import Path

from quart import Quart, jsonify, request


app = Quart(__name__)

BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "user_data" / "users.json"
SECRET_FILE = BASE_DIR / "shared" / "secret_uuid.txt"


# Cargar o generar un UUID secreto para la aplicación
def cargar_secreto():
    SECRET_FILE.parent.mkdir(parents=True, exist_ok=True)

    if SECRET_FILE.exists():
        return uuid.UUID(SECRET_FILE.read_text(encoding="utf-8").strip())

    secreto = uuid.uuid4()
    SECRET_FILE.write_text(str(secreto), encoding="utf-8")
    return secreto


SECRET_UUID = cargar_secreto()


# Funciones auxiliares para manejar autenticacion, usuarios y su persistencia en ficheros
def cargar_usuarios():
    if not USERS_FILE.exists():
        return {}

    with USERS_FILE.open("r", encoding="utf-8") as fichero:
        return json.load(fichero)


def guardar_usuarios(usuarios):
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    

    with USERS_FILE.open("w", encoding="utf-8") as fichero:
        json.dump(usuarios, fichero)

    USERS_FILE.replace(USERS_FILE)


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def generar_token(uid):
    return str(uuid.uuid5(SECRET_UUID, uid))


def credenciales_validas(datos):
    return (
        isinstance(datos, dict)
        and isinstance(datos.get("name"), str)
        and bool(datos["name"].strip())
        and isinstance(datos.get("password"), str)
        and bool(datos["password"])
    )


def usuario_del_token(usuarios, cabecera):
    if not cabecera.startswith("Bearer "):
        return None

    token = cabecera[len("Bearer "):].strip()

    for nombre, datos in usuarios.items():
        if generar_token(datos["uid"]) == token:
            return nombre

    return None


# Funciones de la API para crear, iniciar sesión y modificar usuarios 

@app.put("/user")
async def create_user():
    datos = await request.get_json(silent=True)

    if not credenciales_validas(datos):
        return jsonify({"error": "Nombre o contraseña no válidos"}), 400

    nombre = datos["name"]
    password = datos["password"]
    usuarios = cargar_usuarios()

    if nombre in usuarios:
        return jsonify({"error": "El usuario ya existe"}), 409

    uid = str(uuid.uuid4())
    usuarios[nombre] = {"uid": uid, "password_hash": hash_password(password)}
    guardar_usuarios(usuarios)

    return jsonify({"uid": uid, "token": generar_token(uid)}), 201


@app.post("/user")
async def login():
    datos = await request.get_json(silent=True)

    if not credenciales_validas(datos):
        return jsonify({"error": "Nombre o contraseña no válidos"}), 400

    usuarios = cargar_usuarios()
    usuario = usuarios.get(datos["name"])

    if usuario is None or usuario["password_hash"] != hash_password(datos["password"]):
        return jsonify({"error": "Credenciales incorrectas"}), 401

    uid = usuario["uid"]
    return jsonify({"uid": uid, "token": generar_token(uid)}), 200


@app.patch("/user")
async def modify_user():
    datos = await request.get_json(silent=True)

    if not isinstance(datos, dict) or not isinstance(datos.get("password"), str) or not datos["password"]:
        return jsonify({"error": "Contraseña no válida"}), 400

    usuarios = cargar_usuarios()
    nombre = usuario_del_token(usuarios, request.headers.get("Authorization", ""))

    if nombre is None:
        return jsonify({"error": "Token inválido o ausente"}), 401

    usuarios[nombre]["password_hash"] = hash_password(datos["password"])
    guardar_usuarios(usuarios)

    return jsonify({"message": "Contraseña actualizada"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
