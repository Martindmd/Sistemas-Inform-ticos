from quart import Quart, jsonify, request

from pathlib import Path
import uuid



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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5051)
