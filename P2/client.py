import uuid


import requests


URL_USER = "http://localhost:5050/user"
URL_API = "http://localhost:5051"
resultados_usr = []


def peticion(metodo, datos=None, token=None):
    headers = {}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    return requests.request(metodo, URL_USER, json=datos, headers=headers, timeout=5)

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
    nombre = f"prueba_{uuid.uuid4().hex[:10]}"
    password = "1234"
    nueva_password = "5678"


    respuesta = peticion("PUT", {"name": nombre, "password": password})
    datos = leer_json(respuesta)
    uid, token = datos.get("uid"), datos.get("token")
    correcto = comprobar("Crear usuario", respuesta, 201, bool(uid and token))
    if not correcto:
        return
    resultados_usr.append(correcto)

    respuesta = peticion("PUT", {"name": nombre, "password": password})
    correcto = comprobar("Usuario duplicado", respuesta, 409)
    resultados_usr.append(correcto)


    respuesta = peticion("PUT", {"name": nombre})
    correcto = comprobar("Registro sin contraseña", respuesta, 400)
    resultados_usr.append(correcto)

    respuesta = peticion("PUT", {"name": " ", "password": password})
    correcto = comprobar("Registro con nombre vacío", respuesta, 400)
    resultados_usr.append(correcto)

    respuesta = peticion("PUT", {"name": 123, "password": password})
    correcto = comprobar("Registro con nombre incorrecto", respuesta, 400)
    resultados_usr.append(correcto)

    respuesta = peticion("POST", {"name": nombre, "password": password})
    datos = leer_json(respuesta)
    correcto =comprobar("Login correcto", respuesta, 200,
              datos.get("uid") == uid and datos.get("token") == token)
    resultados_usr.append(correcto)

    respuesta = peticion("POST", {"name": nombre, "password": "incorrecta"})
    correcto = comprobar("Login con contraseña incorrecta", respuesta, 401)
    resultados_usr.append(correcto)

    respuesta = peticion("POST", {"name": f"{nombre}_no_existe", "password": password})
    correcto = comprobar("Login con usuario inexistente", respuesta, 401)
    resultados_usr.append(correcto)

    respuesta = peticion("POST", {"name": nombre})
    correcto = comprobar("Login sin contraseña", respuesta, 400)
    resultados_usr.append(correcto)

    respuesta = peticion("PATCH", {"password": nueva_password})
    correcto =comprobar("Cambio de contraseña sin token", respuesta, 401)
    resultados_usr.append(correcto)

    respuesta = peticion("PATCH", {"password": nueva_password}, "token_falso")
    correcto = comprobar("Cambio de contraseña con token falso", respuesta, 401)
    resultados_usr.append(correcto)

    respuesta = peticion("PATCH", {}, token)
    correcto = comprobar("Cambio sin nueva contraseña", respuesta, 400)
    resultados_usr.append(correcto)

    respuesta = peticion("PATCH", {"password": nueva_password}, token)
    correcto = comprobar("Cambiar contraseña", respuesta, 200)
    resultados_usr.append(correcto)

    respuesta = peticion("POST", {"name": nombre, "password": password})
    correcto = comprobar("Login con contraseña anterior", respuesta, 401)
    resultados_usr.append(correcto)

    respuesta = peticion("POST", {"name": nombre, "password": nueva_password})
    datos = leer_json(respuesta)
    correcto = comprobar("Login con contraseña nueva", respuesta, 200,
              datos.get("uid") == uid and datos.get("token") == token)
    resultados_usr.append(correcto)

    return uid, token

def main():
    print("--- PRUEBAS DE USUARIOS ---")
    credenciales = None
    try:
        credenciales = probar_usuarios()
    except requests.RequestException as error:
        print(f"Error de conexión: {error}")
        print("Comprueba que user.py está ejecutándose en el puerto 5050.")

    correctas_usr = sum(resultados_usr)
    total_usr = len(resultados_usr)
    print(f"\nResultado: {correctas_usr}/{total_usr} pruebas superadas")
    if total_usr < 15:
        print(f"AVISO: No se pudieron completar las 15 pruebas (ejecutadas: {total_usr}).")



if __name__ == "__main__":
    main()