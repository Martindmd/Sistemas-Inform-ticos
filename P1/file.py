from quart import Quart, jsonify, request

from pathlib import Path
import uuid
import json



app = Quart(__name__)


################ FUNCIONES AUXILIARES ###############

def leer_secreto():
    path = Path("shared/secret_uuid.txt")
    try:
         with open(path, 'r') as file:
              return uuid.UUID(file.readlines()[0])
    except FileNotFoundError:
         print("ERROR: Fichero de secreto no encontrado")
         return None

def autorizar_vista(uid):
    code = request.headers.get('Authorization')
    encrypted_uuid = leer_secreto()
    if code is None or not code.startswith("Bearer ") or encrypted_uuid is None:
         return -1
    token = uuid.uuid5(encrypted_uuid, uid)
    if str(token) != code[7:]:
         return -1
    else:
         return 1

def leer_visibilidad(uid):
    path = Path("./visibilidad/" + str(uid) + ".json")
    try:
         with open(path, 'r') as file:
              return json.load(file)
    except FileNotFoundError:
         return {}

def guardar_visibilidad(uid, visibilidad):
    Path("./visibilidad").mkdir(exist_ok=True)
    path = Path("./visibilidad/" + str(uid) + ".json")
    with open(path, 'w') as file:
         json.dump(visibilidad, file)

################ FUNCIONES PRINCIPALES #################


@app.route('/file/<uid>', methods=["GET"])


async def get_user_document_list(uid):
    dirs_list = []
    if autorizar_vista(uid) == -1:
        response = {"error": "Acceso no autorizado"}
        return jsonify(response), 401
    path = Path("./file/" + str(uid))
    try:
        for path in list(path.iterdir()):
             dirs_list.append(path.name)
    except FileNotFoundError:
        pass
    response = {"files": dirs_list}
    return jsonify(response), 200

@app.route('/file/<uid>/<filename>', methods=["PUT"])


async def put_user_document(uid, filename):
    status = None
    msg = ""
    if autorizar_vista(uid) == -1:
        response = {"error": "Acceso no autorizado"}
        return jsonify(response), 401
    entrada = await request.get_json(silent=True)
    if not isinstance(entrada, dict) or not isinstance(entrada.get("text"), str):
        response = {"error": "Falta el campo text o no es una cadena"}
        return jsonify(response), 400
    new_file = entrada["text"]
    Path("./file/" + str(uid)).mkdir(parents=True, exist_ok=True)
    path = Path("./file/" + str(uid) + "/" + filename)
    with open(path, 'w') as file:
        file.write(new_file)
        msg = "Documento actualizado con exito"
        status = 200
    response = {"message": msg}
    return jsonify(response), status 

@app.route('/file/<uid>/<filename>', methods=["GET"])


async def get_user_document(uid, filename):
    visibilidad = leer_visibilidad(uid)
    if visibilidad.get(filename, False) == False and autorizar_vista(uid) == -1:
        response = {"error": "Acceso no autorizado"}
        return jsonify(response), 401
    path = Path('./file/' + str(uid) + "/" + str(filename))
    try:
        with open(path,'r') as file:
            msg = file.read()
    except FileNotFoundError:
        response = {"error": "Documento no encontrado"}
        return jsonify(response), 404
    response = {"message": msg}
    return jsonify(response), 200

@app.route('/file/<uid>/<filename>',methods=["DELETE"])


async def delete_user_document(uid, filename):
    if autorizar_vista(uid) == -1:
        response = {"error": "Acceso no autorizado"}
        return jsonify(response), 401
    path = Path('./file/' + str(uid) + "/" + str(filename))
    try:
        Path.unlink(path)
    except FileNotFoundError:
        response = {"error": "Documento no encontrado"}
        return jsonify(response), 404
    visibilidad = leer_visibilidad(uid)
    visibilidad.pop(filename, None)
    guardar_visibilidad(uid, visibilidad)
    response = {"message": "Archivo eliminado con exito"}
    return jsonify(response), 200

@app.route('/file/<uid>/<filename>', methods=["PATCH"])


async def public_user_document(uid, filename):
    if autorizar_vista(uid) == -1:
        response = {"error": "Acceso no autorizado"}
        return jsonify(response), 401
    path = Path('./file/' + str(uid) + "/" + str(filename))
    if not path.exists():
        response = {"error": "Documento no encontrado"}
        return jsonify(response), 404
    entrada = await request.get_json(silent=True)
    if not isinstance(entrada, dict) or not isinstance(entrada.get("public"), bool):
        response = {"error": "Falta el campo public o no es true/false"}
        return jsonify(response), 400
    visibilidad = leer_visibilidad(uid)
    visibilidad[filename] = entrada["public"]
    guardar_visibilidad(uid, visibilidad)
    response = {"message": "Estado de privacidad de archivo modificado con exito"}
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5051)