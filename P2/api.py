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

@app.route('/peliculas/<int:pelicula_id>/valoracion', methods=["PUT"])


async def votar_pelicula(pelicula_id):
    entrada = await request.get_json(silent=True)
    if not isinstance(entrada, dict):
        response = {"error": "Falta el campo puntuacion"}
        return jsonify(response), 400
    try:
        async with engine.begin() as conn:
            uid = await usuario_del_token(conn)
            if uid is None:
                response = {"error": "Acceso no autorizado"}
                return jsonify(response), 401
            # Si el usuario ya había votado la película se cambia su voto
            resultado = await conn.execute(
                text("INSERT INTO Valoracion (usuario_id, pelicula_id, puntuacion) "
                     "SELECT :uid, id, :puntuacion FROM Pelicula WHERE id = :pelicula AND activa "
                     "ON CONFLICT (usuario_id, pelicula_id) DO UPDATE SET puntuacion = EXCLUDED.puntuacion"),
                {"uid": uid, "pelicula": pelicula_id, "puntuacion": entrada.get("puntuacion")}
            )
    except DBAPIError:
        # Puntuación ausente, que no es un entero o fuera de 0-10 (CHECK)
        response = {"error": "La puntuación debe ser un entero entre 0 y 10"}
        return jsonify(response), 400
    if resultado.rowcount == 0:
        response = {"error": "Película no encontrada"}
        return jsonify(response), 404
    response = {"message": "Valoración guardada con exito"}
    return jsonify(response), 200

@app.route('/carrito', methods=["GET"])


async def get_carrito():
    async with engine.connect() as conn:
        uid = await usuario_del_token(conn)
        if uid is None:
            response = {"error": "Acceso no autorizado"}
            return jsonify(response), 401
        resultado = await conn.execute(
            text("SELECT pe.total, pp.pelicula_id, p.titulo, pp.cantidad, pp.precio_unitario "
                 "FROM Pedido pe "
                 "JOIN PedidoPelicula pp ON pp.pedido_id = pe.id "
                 "JOIN Pelicula p ON p.id = pp.pelicula_id "
                 "WHERE pe.usuario_id = :uid AND pe.estado = 'pendiente' "
                 "ORDER BY p.titulo"),
            {"uid": uid}
        )
        filas = resultado.mappings().all()
    # Todas las filas llevan el total del carrito, se coge de la primera (0 si el carrito está vacío)
    total = filas[0]["total"] if filas else 0
    peliculas = [{"pelicula_id": fila["pelicula_id"], "titulo": fila["titulo"],
                  "cantidad": fila["cantidad"], "precio_unitario": fila["precio_unitario"]}
                 for fila in filas]
    response = {"peliculas": peliculas, "total": total}
    return jsonify(response), 200

@app.route('/carrito', methods=["POST"])


async def add_carrito():
    entrada = await request.get_json(silent=True)
    if not isinstance(entrada, dict):
        response = {"error": "Falta el campo pelicula_id"}
        return jsonify(response), 400
    try:
        async with engine.begin() as conn:
            uid = await usuario_del_token(conn)
            if uid is None:
                response = {"error": "Acceso no autorizado"}
                return jsonify(response), 401
            # El procedimiento crea el carrito si no existe; el trigger resta stock y recalcula el total
            await conn.execute(
                text("CALL anadir_al_carrito(:uid, :pelicula, :cantidad)"),
                {"uid": uid, "pelicula": entrada.get("pelicula_id"), "cantidad": entrada.get("cantidad", 1)}
            )
    except DBAPIError as error:
        # Los errores de los triggers y procedimientos llegan con el texto del RAISE EXCEPTION
        if "Película no disponible" in str(error):
            response = {"error": "Película no disponible"}
            return jsonify(response), 404
        if "Stock insuficiente" in str(error):
            response = {"error": "Stock insuficiente"}
            return jsonify(response), 409
        response = {"error": "Película o cantidad no válidas"}
        return jsonify(response), 400
    response = {"message": "Película añadida al carrito"}
    return jsonify(response), 200

@app.route('/carrito/<int:pelicula_id>', methods=["DELETE"])


async def delete_carrito(pelicula_id):
    async with engine.begin() as conn:
        uid = await usuario_del_token(conn)
        if uid is None:
            response = {"error": "Acceso no autorizado"}
            return jsonify(response), 401
        # El trigger devuelve las unidades al stock y recalcula el total
        resultado = await conn.execute(
            text("DELETE FROM PedidoPelicula "
                 "WHERE pelicula_id = :pelicula "
                 "AND pedido_id = (SELECT id FROM Pedido WHERE usuario_id = :uid AND estado = 'pendiente')"),
            {"uid": uid, "pelicula": pelicula_id}
        )
    if resultado.rowcount == 0:
        response = {"error": "La película no está en el carrito"}
        return jsonify(response), 404
    response = {"message": "Película quitada del carrito"}
    return jsonify(response), 200

@app.route('/carrito/pagar', methods=["POST"])


async def pagar_carrito():
    try:
        async with engine.begin() as conn:
            uid = await usuario_del_token(conn)
            if uid is None:
                response = {"error": "Acceso no autorizado"}
                return jsonify(response), 401
            # El procedimiento guarda la fecha de pago; el trigger descuenta el saldo
            await conn.execute(text("CALL pagar_carrito(:uid)"), {"uid": uid})
    except DBAPIError as error:
        if "Saldo insuficiente" in str(error):
            response = {"error": "Saldo insuficiente"}
            return jsonify(response), 409
        # El usuario no tiene carrito o lo ha dejado vacío
        response = {"error": "El carrito está vacío"}
        return jsonify(response), 400
    response = {"message": "Carrito pagado con exito"}
    return jsonify(response), 200

@app.route('/ventas/<int:anio>/<pais>', methods=["GET"])


async def get_ventas(anio, pais):
    # Esta consulta no va en un procedimiento para poder estudiarla con EXPLAIN (optimizacion.sql)
    async with engine.connect() as conn:
        resultado = await conn.execute(
            text("SELECT pe.id AS pedido_id, u.nombre AS usuario, pe.fecha_pago, pe.total "
                 "FROM Pedido pe "
                 "JOIN Usuario u ON u.id = pe.usuario_id "
                 "WHERE pe.estado = 'pagado' "
                 "AND u.pais = :pais "
                 "AND EXTRACT(YEAR FROM pe.fecha_pago) = :anio "
                 "ORDER BY pe.fecha_pago"),
            {"pais": pais, "anio": anio}
        )
        ventas = [dict(fila) for fila in resultado.mappings()]
    response = {"ventas": ventas}
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5051)
