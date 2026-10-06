from quart import Quart, jsonify

app = Quart(__name__)

@app.route('/file')

async def file(uid):
    response = {"message": "Hola Mundo"}
    return jsonify(response)

"""@app.route('/file')

async def put_user_document(uid, filename):
    return jsonify("put_user_document")

@app.route('/file')

async def get_user_document(uid, filename):
    return jsonify("get_user_document")

@app.route('/file')

async def delete_user_document(uid, filename):
    return jsonify("delete_user_document")

@app.route('/file')

async def public_user_document(uid, filename, public):
    return jsonify("public_use_document")
"""
if __name__ == '__main__':
    app.run(host='localhost', port=5050)