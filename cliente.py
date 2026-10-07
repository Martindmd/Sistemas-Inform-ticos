import uuid

import requests


URL_USER = "http://127.0.0.1:5050/user"
URL_FILE = "http://127.0.0.1:5051/file"
resultados = []


def peticion(metodo, datos=None, token=None):
    headers = {}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    return requests.request(metodo, URL_USER, json=datos, headers=headers, timeout=5)

def peticion_file(metodo, datos=None, token=None):
    headers = {}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
        return requests.request(metodo, URL_FILE, json=datos, headers=headers, timeout=5)


def leer_json(respuesta):
    try:
        datos = respuesta.json()
        return datos if isinstance(datos, dict) else {}
    except ValueError:
        return {}


def comprobar(nombre, respuesta, esperado, condicion=True):
    correcto = respuesta.status_code == esperado and condicion
    resultados.append(correcto)
    estado = "OK" if correcto else "FALLO"
    print(f"[{estado}] {nombre} (HTTP {respuesta.status_code}, esperado {esperado})")
    if not correcto:
        print(f"       Respuesta: {respuesta.text}")
    return correcto


def probar_usuarios():
    nombre = f"prueba_{uuid.uuid4().hex[:10]}"
    password = "1234"
    nueva_password = "5678"

    respuesta = peticion("PUT", {"name": nombre, "password": password})
    datos = leer_json(respuesta)
    uid, token = datos.get("uid"), datos.get("token")
    if not comprobar("Crear usuario", respuesta, 201, bool(uid and token)):
        return

    respuesta = peticion("PUT", {"name": nombre, "password": password})
    comprobar("Usuario duplicado", respuesta, 409)

    respuesta = peticion("PUT", {"name": nombre})
    comprobar("Registro sin contraseña", respuesta, 400)

    respuesta = peticion("PUT", {"name": " ", "password": password})
    comprobar("Registro con nombre vacío", respuesta, 400)

    respuesta = peticion("PUT", {"name": 123, "password": password})
    comprobar("Registro con nombre incorrecto", respuesta, 400)

    respuesta = peticion("POST", {"name": nombre, "password": password})
    datos = leer_json(respuesta)
    comprobar("Login correcto", respuesta, 200,
              datos.get("uid") == uid and datos.get("token") == token)

    respuesta = peticion("POST", {"name": nombre, "password": "incorrecta"})
    comprobar("Login con contraseña incorrecta", respuesta, 401)

    respuesta = peticion("POST", {"name": f"{nombre}_no_existe", "password": password})
    comprobar("Login con usuario inexistente", respuesta, 401)

    respuesta = peticion("POST", {"name": nombre})
    comprobar("Login sin contraseña", respuesta, 400)

    respuesta = peticion("PATCH", {"password": nueva_password})
    comprobar("Cambio de contraseña sin token", respuesta, 401)

    respuesta = peticion("PATCH", {"password": nueva_password}, "token_falso")
    comprobar("Cambio de contraseña con token falso", respuesta, 401)

    respuesta = peticion("PATCH", {}, token)
    comprobar("Cambio sin nueva contraseña", respuesta, 400)

    respuesta = peticion("PATCH", {"password": nueva_password}, token)
    comprobar("Cambiar contraseña", respuesta, 200)

    respuesta = peticion("POST", {"name": nombre, "password": password})
    comprobar("Login con contraseña anterior", respuesta, 401)

    respuesta = peticion("POST", {"name": nombre, "password": nueva_password})
    datos = leer_json(respuesta)
    comprobar("Login con contraseña nueva", respuesta, 200,
              datos.get("uid") == uid and datos.get("token") == token)

def probar_files():
    return None

def main():
    print("--- PRUEBAS DE USUARIOS ---")
    try:
        probar_usuarios()
    except requests.RequestException as error:
        print(f"Error de conexión: {error}")
        print("Comprueba que user.py está ejecutándose en el puerto 5050.")

    correctas = sum(resultados)
    total = len(resultados)
    print(f"\nResultado: {correctas}/{total} pruebas superadas")
    if total < 15:
        print(f"AVISO: No se pudieron completar las 15 pruebas (ejecutadas: {total}).")


if __name__ == "__main__":
    main()
