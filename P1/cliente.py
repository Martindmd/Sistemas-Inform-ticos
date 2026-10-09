import uuid


import requests


URL_USER = "http://localhost:5050/user"
URL_FILE = "http://localhost:5051/file"
resultados_usr = []
resultados_file = []


def peticion(metodo, datos=None, token=None):
    headers = {}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    return requests.request(metodo, URL_USER, json=datos, headers=headers, timeout=5)

def peticion_file(metodo, url, datos=None, token=None):
    headers = {}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    return requests.request(metodo, URL_FILE + url, json=datos, headers=headers, timeout=5)

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

def probar_files(uid, token):
    usr_uid = "/" + uid
    texto = "abababab"
    nuevo_texto = "cdcdcdcd"

    respuesta = peticion("PUT", {"name": f"otro_{uuid.uuid4().hex[:10]}", "password": "1234"})
    token_otro = leer_json(respuesta).get("token")
    correcto = comprobar("Crear segundo usuario", respuesta, 201, bool(token_otro))
    resultados_file.append(correcto)
    if not correcto:
        return

    respuesta = peticion_file("GET", usr_uid, None, token)
    correcto = comprobar("Listar directorio vacío", respuesta, 200,
              leer_json(respuesta).get("files") == [])
    resultados_file.append(correcto)

    respuesta = peticion_file("GET", usr_uid)
    correcto = comprobar("Listar directorio sin token", respuesta, 401)
    resultados_file.append(correcto)

    respuesta = peticion_file("GET", usr_uid, None, token_otro)
    correcto = comprobar("Listar directorio de otro usuario", respuesta, 401)
    resultados_file.append(correcto)

    respuesta = peticion_file("PUT", usr_uid + "/test.txt", {"text": texto}, token)
    correcto = comprobar("Crear fichero", respuesta, 200)
    resultados_file.append(correcto)

    respuesta = peticion_file("PUT", usr_uid + "/test.txt", {"text": nuevo_texto}, token)
    correcto = comprobar("Reescritura de fichero", respuesta, 200)
    resultados_file.append(correcto)

    respuesta = peticion_file("PUT", usr_uid + "/test.txt", {}, token)
    correcto = comprobar("Crear fichero sin texto", respuesta, 400)
    resultados_file.append(correcto)

    respuesta = peticion_file("PUT", usr_uid + "/test.txt", {"text": texto}, token_otro)
    correcto = comprobar("Crear fichero en directorio de otro usuario", respuesta, 401)
    resultados_file.append(correcto)

    respuesta = peticion_file("GET", usr_uid, None, token)
    correcto = comprobar("Listar directorio con un fichero", respuesta, 200,
              leer_json(respuesta).get("files") == ["test.txt"])
    resultados_file.append(correcto)

    respuesta = peticion_file("GET", usr_uid + "/test.txt", None, token)
    correcto = comprobar("Conseguir fichero propio", respuesta, 200,
              leer_json(respuesta).get("message") == nuevo_texto)
    resultados_file.append(correcto)

    respuesta = peticion_file("GET", usr_uid + "/test.txt")
    correcto = comprobar("Conseguir fichero privado sin token", respuesta, 401)
    resultados_file.append(correcto)

    respuesta = peticion_file("GET", usr_uid + "/test.txt", None, token_otro)
    correcto = comprobar("Conseguir fichero privado de otro usuario", respuesta, 401)
    resultados_file.append(correcto)

    respuesta = peticion_file("GET", usr_uid + "/no_existe.txt", None, token)
    correcto = comprobar("Conseguir fichero inexistente", respuesta, 404)
    resultados_file.append(correcto)

    respuesta = peticion_file("PATCH", usr_uid + "/test.txt", {"public": True}, token_otro)
    correcto = comprobar("Cambiar privacidad de fichero de otro usuario", respuesta, 401)
    resultados_file.append(correcto)

    respuesta = peticion_file("PATCH", usr_uid + "/test.txt", {"public": "si"}, token)
    correcto = comprobar("Cambiar privacidad con valor no válido", respuesta, 400)
    resultados_file.append(correcto)

    respuesta = peticion_file("PATCH", usr_uid + "/no_existe.txt", {"public": True}, token)
    correcto = comprobar("Cambiar privacidad de fichero inexistente", respuesta, 404)
    resultados_file.append(correcto)

    respuesta = peticion_file("PATCH", usr_uid + "/test.txt", {"public": True}, token)
    correcto = comprobar("Hacer público el fichero", respuesta, 200)
    resultados_file.append(correcto)

    respuesta = peticion_file("GET", usr_uid + "/test.txt")
    correcto = comprobar("Conseguir fichero público sin token", respuesta, 200,
              leer_json(respuesta).get("message") == nuevo_texto)
    resultados_file.append(correcto)

    respuesta = peticion_file("GET", usr_uid + "/test.txt", None, token_otro)
    correcto = comprobar("Conseguir fichero público de otro usuario", respuesta, 200,
              leer_json(respuesta).get("message") == nuevo_texto)
    resultados_file.append(correcto)

    respuesta = peticion_file("PATCH", usr_uid + "/test.txt", {"public": False}, token)
    correcto = comprobar("Hacer privado el fichero", respuesta, 200)
    resultados_file.append(correcto)

    respuesta = peticion_file("GET", usr_uid + "/test.txt")
    correcto = comprobar("Conseguir fichero de nuevo privado sin token", respuesta, 401)
    resultados_file.append(correcto)

    respuesta = peticion_file("DELETE", usr_uid + "/test.txt", None, token_otro)
    correcto = comprobar("Borrar fichero de otro usuario", respuesta, 401)
    resultados_file.append(correcto)

    respuesta = peticion_file("DELETE", usr_uid + "/test.txt", None, token)
    correcto = comprobar("Borrar fichero", respuesta, 200)
    resultados_file.append(correcto)

    respuesta = peticion_file("DELETE", usr_uid + "/test.txt", None, token)
    correcto = comprobar("Borrar fichero ya borrado", respuesta, 404)
    resultados_file.append(correcto)

    respuesta = peticion_file("GET", usr_uid, None, token)
    correcto = comprobar("Listar directorio tras borrar", respuesta, 200,
              leer_json(respuesta).get("files") == [])
    resultados_file.append(correcto)

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

    print("--- PRUEBAS DE FILES ---")
    if credenciales is None:
        print("No se pueden probar los ficheros sin un usuario válido.")
    else:
        try:
            probar_files(credenciales[0], credenciales[1])
        except requests.RequestException as error:
            print(f"Error de conexión: {error}")
            print("Comprueba que file.py está ejecutándose en el puerto 5051.")

    correctas_file = sum(resultados_file)
    total_file = len(resultados_file)
    print(f"\nResultado: {correctas_file}/{total_file} pruebas superadas")
    if total_file < 25:
        print(f"AVISO: No se pudieron completar las 25 pruebas (ejecutadas: {total_file}).")


if __name__ == "__main__":
    main()