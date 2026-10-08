from quart import Quart, jsonify, request

from pathlib import Path
import uuid



app = Quart(__name__)

################ FUNCIONES AUXILIARES ###############

def autorizar_vista(uid, status, msg):
    return 1
    """code = request.headers.get('Authorization')
    saved_token = uuid.UUID(code[7:])
    encrypted_uuid = None
    token = uuid.uuid4(encrypted_uuid, uid)
    if token != saved_token:
         status = 401
         msg = "ERROR: Acceso no autorizado"
         return -1
    else:
         return 1"""

################ FUNCIONES PRINCIPALES #################

@app.route('/file/<uid>', methods=["GET"])

async def get_user_document_list(uid):
    status = None
    msg = ""
    dirs_list = []
    if autorizar_vista(uid, status, msg) == -1:
        response = {"message": msg}
        return jsonify(response), status 
    path = Path("./file/" + str(uid))
    try:
        for path in list(path.iterdir()):
             dirs_list.append(str(path))
        msg = str(dirs_list)
        status = 200
    except FileNotFoundError:
        msg = "Error, Directorio no encontrado"
        status = 404
    response = {"message": msg}
    return jsonify(response), status 

@app.route('/file/<uid>/<filename>', methods=["PUT"])

async def put_user_document(uid, filename):
    status = None
    msg = ""
    if autorizar_vista(uid, status, msg) == -1:
        response = {"message": msg}
        return jsonify(response), status 
    entrada = await request.get_json()
    new_file = entrada["text"]
    path = Path("./file/" + str(uid) + "/" + filename)
    try:
        with open(path, 'w') as file:
            file.write(new_file)
            msg = "Documento actualizado con exito"
            status = 200
    except FileNotFoundError:
        msg = "Error, Directorio no encontrado"
        status = 404
    response = {"message": msg}
    return jsonify(response), status 

@app.route('/file/<uid>/<filename>', methods=["GET"])

async def get_user_document(uid, filename):
    status = None
    msg = ""
    if autorizar_vista(uid, status, msg) == -1:
        response = {"message": msg}
        return jsonify(response), status 
    path = Path('./file/' + str(uid) + "/" + str(filename))
    try:
        with open(path,'r') as file:
            msg = file.read()
            status = 200
    except FileNotFoundError:
        msg = "Error, Directorio no encontrado"
        status = 404
    response = {"message": msg}
    return jsonify(response), status 

@app.route('/file/<uid>/<filename>',methods=["DELETE"])

async def delete_user_document(uid, filename):
    status = None
    msg = ""
    if autorizar_vista(uid, status, msg) == -1:
        response = {"message": msg}
        return jsonify(response), status 
    path = Path('./file/' + str(uid) + "/" + str(filename))
    try:
        Path.unlink(path)
        msg = "Archivo eliminado con exito"
        status = 200
    except FileNotFoundError:
            msg = "Error, Directorio no encontrado"
            status = 404
    response = {"message": msg}
    return jsonify(response), status

@app.route('/file/<uid>/<filename>', methods=["PATCH"])

async def public_user_document(uid, filename, public):
    status = None
    msg = ""
    if autorizar_vista(uid, status, msg) == -1:
        response = {"message": msg}
        return jsonify(response), status 
    path = Path('./file/' + str(uid) + "/" + str(filename))
    try:
            msg = "Estado de privacidad de archivo modificado con exito"
            status = 200
    except FileNotFoundError:
                msg = "Error, Directorio no encontrado"
                status = 404
    response = {"message": msg}
    return jsonify(response), status

if __name__ == '__main__':
    path = Path("shared/secret_uuid.txt")
    try:
         with open(path, 'r') as file:
              encrypted_uuid = uuid.UUID(file.readlines()[0])
    except FileNotFoundError:
         print("ERROR: encrypted uid file not found")
    app.run(host='localhost', port=5051)