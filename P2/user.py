import hashlib
import os
import uuid
from pathlib import Path

from quart import Quart, jsonify, request
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine


app = Quart(__name__)

BASE_DIR = Path(__file__).resolve().parent
SECRET_FILE = BASE_DIR / "shared" / "secret_uuid.txt"

# En Docker la URL llega por la variable de entorno; en local se usa la base de datos expuesta en localhost
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://alumnodb:1234@localhost:5432/si1")
engine = create_async_engine(DATABASE_URL, echo=False)


# Cargar o generar un UUID secreto para la aplicación
def cargar_secreto():
    SECRET_FILE.parent.mkdir(parents=True, exist_ok=True)

    if SECRET_FILE.exists():
        return uuid.UUID(SECRET_FILE.read_text(encoding="utf-8").strip())

    secreto = uuid.uuid4()
    SECRET_FILE.write_text(str(secreto), encoding="utf-8")
    return secreto


SECRET_UUID = cargar_secreto()


# Funciones auxiliares para manejar autenticacion y usuarios

def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# El token es "<uid>.<uuid5 del secreto con uid y sesion>": al cambiar la sesion (logout) cambia el token
def generar_token(uid, sesion):
    return f"{uid}.{uuid.uuid5(SECRET_UUID, f'{uid}.{sesion}')}"


def credenciales_validas(datos):
    return (
        isinstance(datos, dict)
        and isinstance(datos.get("name"), str)
        and bool(datos["name"].strip())
        and isinstance(datos.get("password"), str)
        and bool(datos["password"])
    )


# Devuelve el id del usuario dueño del token, o None si el token no es válido
async def usuario_del_token(conn, cabecera):
    if cabecera is None or not cabecera.startswith("Bearer "):
        return None

    token = cabecera[len("Bearer "):].strip()
    uid = token.split(".")[0]
    if not uid.isdigit():
        return None

    resultado = await conn.execute(
        text("SELECT sesion FROM Usuario WHERE id = :id"),
        {"id": int(uid)}
    )
    fila = resultado.first()

    if fila is None or generar_token(uid, fila.sesion) != token:
        return None

    return int(uid)


# Funciones de la API para crear, iniciar sesión y modificar usuarios

@app.put("/user")
async def create_user():
    datos = await request.get_json(silent=True)

    if not credenciales_validas(datos) or not isinstance(datos.get("pais"), str) or not datos["pais"].strip():
        return jsonify({"error": "Nombre, contraseña o país no válidos"}), 400

    try:
        async with engine.begin() as conn:
            resultado = await conn.execute(
                text("INSERT INTO Usuario (nombre, password_hash, pais) "
                     "VALUES (:nombre, :password_hash, :pais) RETURNING id, sesion"),
                {"nombre": datos["name"], "password_hash": hash_password(datos["password"]), "pais": datos["pais"]}
            )
            fila = resultado.first()
    except IntegrityError:
        return jsonify({"error": "El usuario ya existe"}), 409

    return jsonify({"uid": fila.id, "token": generar_token(fila.id, fila.sesion)}), 201


@app.post("/user")
async def login():
    datos = await request.get_json(silent=True)

    if not credenciales_validas(datos):
        return jsonify({"error": "Nombre o contraseña no válidos"}), 400

    async with engine.connect() as conn:
        resultado = await conn.execute(
            text("SELECT id, password_hash, sesion FROM Usuario WHERE nombre = :nombre"),
            {"nombre": datos["name"]}
        )
        usuario = resultado.first()

    if usuario is None or usuario.password_hash != hash_password(datos["password"]):
        return jsonify({"error": "Credenciales incorrectas"}), 401

    return jsonify({"uid": usuario.id, "token": generar_token(usuario.id, usuario.sesion)}), 200


@app.post("/user/logout")
async def logout():
    async with engine.begin() as conn:
        uid = await usuario_del_token(conn, request.headers.get("Authorization"))

        if uid is None:
            return jsonify({"error": "Token inválido o ausente"}), 401

        # Al cambiar la sesion el token anterior deja de ser válido
        await conn.execute(
            text("UPDATE Usuario SET sesion = sesion + 1 WHERE id = :id"),
            {"id": uid}
        )

    return jsonify({"message": "Sesión cerrada"}), 200


@app.patch("/user")
async def modify_user():
    datos = await request.get_json(silent=True)

    if not isinstance(datos, dict) or not isinstance(datos.get("password"), str) or not datos["password"]:
        return jsonify({"error": "Contraseña no válida"}), 400

    async with engine.begin() as conn:
        uid = await usuario_del_token(conn, request.headers.get("Authorization"))

        if uid is None:
            return jsonify({"error": "Token inválido o ausente"}), 401

        await conn.execute(
            text("UPDATE Usuario SET password_hash = :password_hash WHERE id = :id"),
            {"password_hash": hash_password(datos["password"]), "id": uid}
        )

    return jsonify({"message": "Contraseña actualizada"}), 200


@app.patch("/user/saldo")
async def recargar_saldo():
    datos = await request.get_json(silent=True)

    if not isinstance(datos, dict) or not isinstance(datos.get("cantidad"), (int, float)) or datos["cantidad"] <= 0:
        return jsonify({"error": "La cantidad debe ser un número positivo"}), 400

    async with engine.begin() as conn:
        uid = await usuario_del_token(conn, request.headers.get("Authorization"))

        if uid is None:
            return jsonify({"error": "Token inválido o ausente"}), 401

        resultado = await conn.execute(
            text("UPDATE Usuario SET saldo = saldo + :cantidad WHERE id = :id RETURNING saldo"),
            {"cantidad": datos["cantidad"], "id": uid}
        )
        saldo = resultado.scalar()

    return jsonify({"saldo": float(saldo)}), 200


@app.delete("/user")
async def delete_user():
    async with engine.begin() as conn:
        uid = await usuario_del_token(conn, request.headers.get("Authorization"))

        if uid is None:
            return jsonify({"error": "Token inválido o ausente"}), 401

        # El procedimiento devuelve al stock lo que hubiera en su carrito y borra sus datos
        await conn.execute(text("CALL borrar_usuario(:id)"), {"id": uid})

    return jsonify({"message": "Usuario borrado"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
