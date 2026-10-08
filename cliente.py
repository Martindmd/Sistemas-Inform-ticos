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
    print (URL_FILE + url)
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


def probar_files():
    usr_uid = "/4d9d97a1-d8a5-4232-a62a-7174cbc87cc8"
    respuesta = peticion_file("GET", usr_uid, None, None)
    correcto = comprobar("Listar directorios", respuesta, 200)
    resultados_file.append(correcto)


    str = "abababab"
    respuesta = peticion_file("PUT", usr_uid +  "/test.txt", {"text": str})
    correcto = comprobar("Reescritura de fichero", respuesta, 200)
    resultados_file.append(correcto)


    respuesta = peticion_file("GET", usr_uid + "/test.txt")
    correcto = comprobar("Conseguir info de fichero", respuesta, 200)
    resultados_file.append(correcto)


    respuesta = peticion_file("PATCH", usr_uid + "/test.txt")
    correcto = comprobar("Cambiar privacidad ", respuesta, 200)
    resultados_file.append(correcto)


    respuesta = peticion_file("DELETE", usr_uid + "/test.txt")
    correcto = comprobar("Borrar fichero", respuesta, 200)
    resultados_file.append(correcto)
def main():
    print("--- PRUEBAS DE USUARIOS ---")
    try:
        probar_usuarios()
    except requests.RequestException as error:
        print(f"Error de conexión: {error}")
        print("Comprueba que user.py está ejecutándose en el puerto 5050.")


    correctas_usr = sum(resultados_usr)
    total_usr = len(resultados_usr)
    print(f"\nResultado: {correctas_usr}/{total_usr} pruebas superadas")
    if total_usr < 15:
        print(f"AVISO: No se pudieron completar las 15 pruebas (ejecutadas: {total_usr}).")


    print("--- PRUEBAS DE FILES ---")
    try:
        probar_files()
    except requests.RequestException as error:
        print(f"Error de conexión: {error}")


    print(resultados_file)
    correctas_file = sum(resultados_file)
    total_file = len(resultados_file)
    print(f"\nResultado: {correctas_file}/{total_file} pruebas superadas")
    if total_file < 5:
        print(f"AVISO: No se pudieron completar las 5 pruebas (ejecutadas: {total_file}).")




if _name_ == "_main_":
    main()