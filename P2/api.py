from quart import Quart, jsonify, request

from pathlib import Path
import os
import uuid

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine



app = Quart(__name__)

# En Docker la URL llega por la variable de entorno; en local se usa la base de datos expuesta en localhost
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://alumnodb:1234@localhost:5432/si1")
engine = create_async_engine(DATABASE_URL, echo=False)


################ FUNCIONES AUXILIARES ###############

def leer_secreto():
    path = Path("shared/secret_uuid.txt")
    try:
         with open(path, 'r') as file:
              return uuid.UUID(file.readlines()[0])
    except FileNotFoundError:
         print("ERROR: Fichero de secreto no encontrado")
         return None

# Devuelve el id del usuario dueño del token, o None si el token no es válido (mismo formato que en user.py)
async def usuario_del_token(conn):
    code = request.headers.get('Authorization')
    secreto = leer_secreto()
    if code is None or not code.startswith("Bearer ") or secreto is None:
         return None
    token = code[7:]
    uid = token.split(".")[0]
    if not uid.isdigit():
         return None
    resultado = await conn.execute(
         text("SELECT sesion FROM Usuario WHERE id = :id"),
         {"id": int(uid)}
    )
    fila = resultado.first()
    if fila is None or token != f"{uid}.{uuid.uuid5(secreto, f'{uid}.{fila.sesion}')}":
         return None
    return int(uid)

################ FUNCIONES PRINCIPALES #################


@app.route('/peliculas', methods=["GET"])


async def get_peliculas():
    # Filtros opcionales: /peliculas?genero=anime&director=nolan&actor=caine
    async with engine.connect() as conn:
        resultado = await conn.execute(
            text("SELECT * FROM buscar_peliculas(:genero, :director, :actor)"),
            {"genero": request.args.get("genero"),
             "director": request.args.get("director"),
             "actor": request.args.get("actor")}
        )
        peliculas = [dict(fila) for fila in resultado.mappings()]
    response = {"peliculas": peliculas}
    return jsonify(response), 200

@app.route('/peliculas/<int:pelicula_id>', methods=["GET"])


async def get_pelicula(pelicula_id):
    async with engine.connect() as conn:
        resultado = await conn.execute(
            text("SELECT p.id, p.titulo, p.anio, p.genero, p.precio, p.stock, d.nombre AS director, "
                 "       obtener_media_pelicula(p.id) AS media, "
                 "       ARRAY(SELECT a.nombre FROM PeliculaActor pa JOIN Actor a ON a.id = pa.actor_id "
                 "             WHERE pa.pelicula_id = p.id ORDER BY a.nombre) AS actores "
                 "FROM Pelicula p JOIN Director d ON d.id = p.director_id "
                 "WHERE p.id = :id AND p.activa"),
            {"id": pelicula_id}
        )
        pelicula = resultado.mappings().first()
    if pelicula is None:
        response = {"error": "Película no encontrada"}
        return jsonify(response), 404
    response = dict(pelicula)
    return jsonify(response), 200

@app.route('/peliculas', methods=["POST"])


async def create_pelicula():
    entrada = await request.get_json(silent=True)
    if not isinstance(entrada, dict):
        response = {"error": "Faltan los datos de la película"}
        return jsonify(response), 400
    try:
        async with engine.begin() as conn:
            if await usuario_del_token(conn) is None:
                response = {"error": "Acceso no autorizado"}
                return jsonify(response), 401
            resultado = await conn.execute(
                text("SELECT crear_pelicula(:titulo, :anio, :genero, :precio, :stock, :director, :actores)"),
                {"titulo": entrada.get("titulo"), "anio": entrada.get("anio"),
                 "genero": entrada.get("genero"), "precio": entrada.get("precio"),
                 "stock": entrada.get("stock"), "director": entrada.get("director"),
                 "actores": entrada.get("actores", [])}
            )
            pelicula_id = resultado.scalar()
    except DBAPIError:
        # Falta algún campo, tiene un tipo incorrecto o no cumple un CHECK (precio o stock negativos)
        response = {"error": "Datos de la película no válidos"}
        return jsonify(response), 400
    response = {"id": pelicula_id}
    return jsonify(response), 201

@app.route('/peliculas/<int:pelicula_id>', methods=["DELETE"])


async def delete_pelicula(pelicula_id):
    async with engine.begin() as conn:
        if await usuario_del_token(conn) is None:
            response = {"error": "Acceso no autorizado"}
            return jsonify(response), 401
        # Borrado lógico: la película sale del catálogo pero se conservan sus ventas
        resultado = await conn.execute(
            text("UPDATE Pelicula SET activa = FALSE WHERE id = :id AND activa"),
            {"id": pelicula_id}
        )
    if resultado.rowcount == 0:
        response = {"error": "Película no encontrada"}
        return jsonify(response), 404
    response = {"message": "Película borrada con exito"}
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5051)
