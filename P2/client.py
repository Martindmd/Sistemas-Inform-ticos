import uuid
from datetime import datetime


import requests


URL_USER = "http://localhost:5050/user"
URL_API = "http://localhost:5051"
resultados_usr = []
resultados_pel = []
resultados_compra = []


def peticion(metodo, datos=None, token=None, ruta=""):
    headers = {}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    return requests.request(metodo, URL_USER + ruta, json=datos, headers=headers, timeout=5)

def peticion_api(metodo, url, datos=None, token=None):
    headers = {}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    return requests.request(metodo, URL_API + url, json=datos, headers=headers, timeout=5)

def leer_json(respuesta):
    try:
        datos = respuesta.json()
        return datos if isinstance(datos, dict) else {}
    except ValueError:
        return {}


def comprobar(nombre, respuesta, esperado, condicion=True):
    correcto = respuesta.status_code == esperado and condicion
    estado = "OK" if correcto else "FALLO"
    print(f"[{estado}] {nombre} (HTTP {respuesta.status_code}, esperado {esperado})")
    if not correcto:
        print(f"       Respuesta: {respuesta.text}")
    return correcto


def probar_usuarios():
    # Nombre y país únicos en cada ejecución para que las pruebas se puedan repetir
    nombre = f"prueba_{uuid.uuid4().hex[:10]}"
    pais = f"Pais_{uuid.uuid4().hex[:6]}"
    password = "1234"
    nueva_password = "5678"


    respuesta = peticion("PUT", {"name": nombre, "password": password, "pais": pais})
    datos = leer_json(respuesta)
    uid, token = datos.get("uid"), datos.get("token")
    correcto = comprobar("Crear usuario", respuesta, 201, bool(uid and token))
    resultados_usr.append(correcto)
    if not correcto:
        return

    respuesta = peticion("PUT", {"name": nombre, "password": password, "pais": pais})
    correcto = comprobar("Usuario duplicado", respuesta, 409)
    resultados_usr.append(correcto)

    respuesta = peticion("PUT", {"name": nombre, "pais": pais})
    correcto = comprobar("Registro sin contraseña", respuesta, 400)
    resultados_usr.append(correcto)

    respuesta = peticion("PUT", {"name": f"{nombre}_2", "password": password})
    correcto = comprobar("Registro sin país", respuesta, 400)
    resultados_usr.append(correcto)

    respuesta = peticion("PUT", {"name": " ", "password": password, "pais": pais})
    correcto = comprobar("Registro con nombre vacío", respuesta, 400)
    resultados_usr.append(correcto)

    respuesta = peticion("POST", {"name": nombre, "password": password})
    datos = leer_json(respuesta)
    correcto = comprobar("Login correcto", respuesta, 200,
              datos.get("uid") == uid and datos.get("token") == token)
    resultados_usr.append(correcto)

    respuesta = peticion("POST", {"name": nombre, "password": "incorrecta"})
    correcto = comprobar("Login con contraseña incorrecta", respuesta, 401)
    resultados_usr.append(correcto)

    respuesta = peticion("POST", {"name": f"{nombre}_no_existe", "password": password})
    correcto = comprobar("Login con usuario inexistente", respuesta, 401)
    resultados_usr.append(correcto)

    respuesta = peticion("PATCH", {"password": nueva_password})
    correcto = comprobar("Cambio de contraseña sin token", respuesta, 401)
    resultados_usr.append(correcto)

    respuesta = peticion("PATCH", {"password": nueva_password}, token)
    correcto = comprobar("Cambiar contraseña", respuesta, 200)
    resultados_usr.append(correcto)

    respuesta = peticion("POST", {"name": nombre, "password": nueva_password})
    correcto = comprobar("Login con contraseña nueva", respuesta, 200)
    resultados_usr.append(correcto)

    respuesta = peticion("PATCH", {"cantidad": 50}, token, "/saldo")
    correcto = comprobar("Recargar saldo", respuesta, 200, leer_json(respuesta).get("saldo") == 50)
    resultados_usr.append(correcto)

    respuesta = peticion("PATCH", {"cantidad": -10}, token, "/saldo")
    correcto = comprobar("Recargar saldo negativo", respuesta, 400)
    resultados_usr.append(correcto)

    respuesta = peticion("PATCH", {"cantidad": 10}, "token_falso", "/saldo")
    correcto = comprobar("Recargar saldo con token falso", respuesta, 401)
    resultados_usr.append(correcto)

    respuesta = peticion("POST", None, token, "/logout")
    correcto = comprobar("Logout", respuesta, 200)
    resultados_usr.append(correcto)

    respuesta = peticion("PATCH", {"cantidad": 10}, token, "/saldo")
    correcto = comprobar("Usar el token tras el logout", respuesta, 401)
    resultados_usr.append(correcto)

    respuesta = peticion("POST", {"name": nombre, "password": nueva_password})
    nuevo_token = leer_json(respuesta).get("token")
    correcto = comprobar("Login tras el logout (token nuevo)", respuesta, 200,
              bool(nuevo_token) and nuevo_token != token)
    resultados_usr.append(correcto)

    return nombre, pais, nuevo_token

def probar_peliculas(token):
    director = f"Director_{uuid.uuid4().hex[:6]}"
    pelicula = {"titulo": "Pelicula de prueba", "anio": 2026, "genero": "Drama", "precio": 30,
                "stock": 3, "director": director, "actores": ["Actor de prueba"]}

    respuesta = peticion_api("GET", "/peliculas")
    correcto = comprobar("Listar catálogo", respuesta, 200, len(leer_json(respuesta).get("peliculas", [])) > 0)
    resultados_pel.append(correcto)

    respuesta = peticion_api("GET", "/peliculas?genero=anime")
    peliculas = leer_json(respuesta).get("peliculas", [])
    correcto = comprobar("Filtrar por género", respuesta, 200,
              len(peliculas) > 0 and all(p["genero"] == "Anime" for p in peliculas))
    resultados_pel.append(correcto)

    respuesta = peticion_api("POST", "/peliculas", pelicula)
    correcto = comprobar("Crear película sin token", respuesta, 401)
    resultados_pel.append(correcto)

    respuesta = peticion_api("POST", "/peliculas", {**pelicula, "precio": -5}, token) # Copia de la película con precio negativo
    correcto = comprobar("Crear película con precio negativo", respuesta, 400)
    resultados_pel.append(correcto)

    respuesta = peticion_api("POST", "/peliculas", {"titulo": "Sin datos"}, token)
    correcto = comprobar("Crear película con datos incompletos", respuesta, 400)
    resultados_pel.append(correcto)

    respuesta = peticion_api("POST", "/peliculas", pelicula, token)
    pelicula_id = leer_json(respuesta).get("id")
    correcto = comprobar("Crear película", respuesta, 201, pelicula_id is not None)
    resultados_pel.append(correcto)
    if not correcto:
        return

    respuesta = peticion_api("GET", f"/peliculas/{pelicula_id}")
    datos = leer_json(respuesta)
    correcto = comprobar("Ver película creada", respuesta, 200,
              datos.get("director") == director and datos.get("actores") == ["Actor de prueba"]
              and datos.get("media") is None)
    resultados_pel.append(correcto)

    respuesta = peticion_api("GET", f"/peliculas?director={director}")
    correcto = comprobar("Filtrar por director", respuesta, 200,
              [p["id"] for p in leer_json(respuesta).get("peliculas", [])] == [pelicula_id])
    resultados_pel.append(correcto)

    respuesta = peticion_api("GET", "/peliculas/999999")
    correcto = comprobar("Ver película inexistente", respuesta, 404)
    resultados_pel.append(correcto)

    respuesta = peticion_api("PUT", f"/peliculas/{pelicula_id}/valoracion", {"puntuacion": 8})
    correcto = comprobar("Votar sin token", respuesta, 401)
    resultados_pel.append(correcto)

    respuesta = peticion_api("PUT", f"/peliculas/{pelicula_id}/valoracion", {"puntuacion": 11}, token)
    correcto = comprobar("Votar con puntuación fuera de rango", respuesta, 400)
    resultados_pel.append(correcto)

    respuesta = peticion_api("PUT", "/peliculas/999999/valoracion", {"puntuacion": 8}, token)
    correcto = comprobar("Votar película inexistente", respuesta, 404)
    resultados_pel.append(correcto)

    respuesta = peticion_api("PUT", f"/peliculas/{pelicula_id}/valoracion", {"puntuacion": 8}, token)
    correcto = comprobar("Votar película", respuesta, 200)
    resultados_pel.append(correcto)

    respuesta = peticion_api("PUT", f"/peliculas/{pelicula_id}/valoracion", {"puntuacion": 6}, token)
    correcto = comprobar("Cambiar el voto", respuesta, 200)
    resultados_pel.append(correcto)

    respuesta = peticion_api("GET", f"/peliculas/{pelicula_id}")
    media = leer_json(respuesta).get("media")
    correcto = comprobar("Puntuación media", respuesta, 200, media is not None and float(media) == 6)
    resultados_pel.append(correcto)

    return pelicula_id

def probar_compras(nombre, pais, token, pelicula_id):
    # El usuario tiene 50 de saldo y la película cuesta 30 (stock 3)
    carrito = f"/carrito/{pelicula_id}"

    respuesta = peticion_api("GET", "/carrito", None, token)
    correcto = comprobar("Ver carrito vacío", respuesta, 200, leer_json(respuesta).get("peliculas") == [])
    resultados_compra.append(correcto)

    respuesta = peticion_api("POST", "/carrito/pagar", None, token)
    correcto = comprobar("Pagar sin carrito", respuesta, 400)
    resultados_compra.append(correcto)

    respuesta = peticion_api("POST", "/carrito", {"pelicula_id": pelicula_id})
    correcto = comprobar("Añadir al carrito sin token", respuesta, 401)
    resultados_compra.append(correcto)

    respuesta = peticion_api("POST", "/carrito", {"pelicula_id": 999999}, token)
    correcto = comprobar("Añadir película inexistente", respuesta, 404)
    resultados_compra.append(correcto)

    respuesta = peticion_api("POST", "/carrito", {"pelicula_id": pelicula_id, "cantidad": 0}, token)
    correcto = comprobar("Añadir cantidad no válida", respuesta, 400)
    resultados_compra.append(correcto)

    respuesta = peticion_api("POST", "/carrito", {"pelicula_id": pelicula_id, "cantidad": 2}, token)
    correcto = comprobar("Añadir 2 unidades al carrito", respuesta, 200)
    resultados_compra.append(correcto)

    respuesta = peticion_api("POST", "/carrito", {"pelicula_id": pelicula_id, "cantidad": 5}, token)
    correcto = comprobar("Añadir más unidades que el stock", respuesta, 409)
    resultados_compra.append(correcto)

    respuesta = peticion_api("GET", "/carrito", None, token)
    datos = leer_json(respuesta)
    correcto = comprobar("Ver carrito (total actualizado)", respuesta, 200,
              len(datos.get("peliculas", [])) == 1 and float(datos.get("total", 0)) == 60)
    resultados_compra.append(correcto)

    respuesta = peticion_api("POST", "/carrito/pagar", None, token)
    correcto = comprobar("Pagar con saldo insuficiente", respuesta, 409)
    resultados_compra.append(correcto)

    respuesta = peticion_api("DELETE", carrito, None, token)
    correcto = comprobar("Quitar película del carrito", respuesta, 200)
    resultados_compra.append(correcto)

    respuesta = peticion_api("DELETE", carrito, None, token)
    correcto = comprobar("Quitar película que no está en el carrito", respuesta, 404)
    resultados_compra.append(correcto)

    respuesta = peticion_api("POST", "/carrito/pagar", None, token)
    correcto = comprobar("Pagar carrito vacío", respuesta, 400)
    resultados_compra.append(correcto)

    respuesta = peticion_api("POST", "/carrito", {"pelicula_id": pelicula_id}, token)
    correcto = comprobar("Añadir 1 unidad al carrito", respuesta, 200)
    resultados_compra.append(correcto)

    respuesta = peticion_api("POST", "/carrito/pagar", None, token)
    correcto = comprobar("Pagar carrito", respuesta, 200)
    resultados_compra.append(correcto)

    respuesta = peticion_api("GET", f"/peliculas/{pelicula_id}")
    correcto = comprobar("Stock actualizado tras la compra", respuesta, 200, leer_json(respuesta).get("stock") == 2)
    resultados_compra.append(correcto)

    respuesta = peticion("PATCH", {"cantidad": 1}, token, "/saldo")
    correcto = comprobar("Saldo descontado tras la compra", respuesta, 200, leer_json(respuesta).get("saldo") == 21)
    resultados_compra.append(correcto)

    respuesta = peticion_api("GET", f"/ventas/{datetime.now().year}/{pais}")
    ventas = leer_json(respuesta).get("ventas", [])
    correcto = comprobar("Ventas del año y país", respuesta, 200,
              len(ventas) == 1 and ventas[0]["usuario"] == nombre and float(ventas[0]["total"]) == 30)
    resultados_compra.append(correcto)

    respuesta = peticion_api("GET", f"/ventas/1990/{pais}")
    correcto = comprobar("Ventas de un año sin compras", respuesta, 200, leer_json(respuesta).get("ventas") == [])
    resultados_compra.append(correcto)

    respuesta = peticion_api("DELETE", f"/peliculas/{pelicula_id}")
    correcto = comprobar("Borrar película sin token", respuesta, 401)
    resultados_compra.append(correcto)

    respuesta = peticion_api("DELETE", f"/peliculas/{pelicula_id}", None, token)
    correcto = comprobar("Borrar película", respuesta, 200)
    resultados_compra.append(correcto)

    respuesta = peticion_api("DELETE", f"/peliculas/{pelicula_id}", None, token)
    correcto = comprobar("Borrar película ya borrada", respuesta, 404)
    resultados_compra.append(correcto)

    respuesta = peticion_api("POST", "/carrito", {"pelicula_id": pelicula_id}, token)
    correcto = comprobar("Añadir película borrada al carrito", respuesta, 404)
    resultados_compra.append(correcto)

    respuesta = peticion("DELETE", None, token)
    correcto = comprobar("Borrar usuario", respuesta, 200)
    resultados_compra.append(correcto)

    respuesta = peticion("DELETE", None, token)
    correcto = comprobar("Borrar usuario ya borrado", respuesta, 401)
    resultados_compra.append(correcto)

def imprimir_resultado(resultados):
    print(f"\nResultado: {sum(resultados)}/{len(resultados)} pruebas superadas\n")

def main():
    print("--- PRUEBAS DE USUARIOS ---")
    credenciales = None
    try:
        credenciales = probar_usuarios()
    except requests.RequestException as error:
        print(f"Error de conexión: {error}")
        print("Comprueba que user.py está ejecutándose en el puerto 5050.")
    imprimir_resultado(resultados_usr)

    if credenciales is None:
        print("No se puede probar la API sin un usuario válido.")
        return
    nombre, pais, token = credenciales

    try:
        print("--- PRUEBAS DE PELÍCULAS Y VALORACIONES ---")
        pelicula_id = probar_peliculas(token)
        imprimir_resultado(resultados_pel)

        print("--- PRUEBAS DE CARRITO, VENTAS Y BORRADO ---")
        if pelicula_id is None:
            print("No se pueden probar las compras sin una película creada.")
        else:
            probar_compras(nombre, pais, token, pelicula_id)
            imprimir_resultado(resultados_compra)
    except requests.RequestException as error:
        print(f"Error de conexión: {error}")
        print("Comprueba que api.py está ejecutándose en el puerto 5051.")

    total = resultados_usr + resultados_pel + resultados_compra
    print(f"TOTAL: {sum(total)}/{len(total)} pruebas superadas")


if __name__ == "__main__":
    main()
