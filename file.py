from quart import Quart, jsonify

app = Quart(__name__)

################ FUNCIONES AUXILIARES ###############

def autorizar_vista(uid):
    return True

################ FUNCIONES PRINCIPALES #################

@app.route('/file/<uid>', methods=["GET"])

async def get_user_document_list(uid):
    response = {"message": "Hola Mundo"}
    return jsonify(response)

@app.route('/file/<uid>/<filename>', methods=["PUT"])

async def put_user_document(uid, filename):
    return jsonify("put_user_document")

@app.route('/file/<uid>/<filename>', methods=["GET"])

async def get_user_document(uid, filename):
    return jsonify("get_user_document")

@app.route('/file/<uid>/<filename>',methods=["DELETE"])

async def delete_user_document(uid, filename):
    return jsonify("delete_user_document")

@app.route('/file/<uid>/<filename>', methods=["PATCH"])

async def public_user_document(uid, filename, public):
    return jsonify("public_use_document")

if __name__ == '__main__':
    app.run(host='localhost', port=5051)