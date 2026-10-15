Practica 2 - Sistemas Informaticos

user.py   -> servicio de usuarios (puerto 5050)
api.py    -> servicio principal del videoclub (puerto 5051)
client.py -> pruebas de los dos servicios

Hay que ejecutar todo desde la carpeta raiz.

Ejecucion local

python3 -m venv venv/si1p2
source venv/si1p2/bin/activate
pip install -r requirements.txt

Luego, cada uno en una terminal (con el entorno activado):

python user.py
python api.py
python client.py

Ejecucion con Docker

docker compose up --build

Y en otra terminal, con el entorno activado:

python client.py

Para pararlo: Ctrl+C y docker compose down

Si falla por favor comprobad que la version de python del ordenador del laboratorio sea la misma que pone en Dockerfile,
ya que nos ha dado algunos problemas mientras comprobabamos en los ordenadores del laboratorio.
