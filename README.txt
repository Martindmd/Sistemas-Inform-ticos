Practica 1 - Sistemas Informaticos

user.py   -> servicio de usuarios (puerto 5050)
file.py   -> servicio de ficheros (puerto 5051)
cliente.py -> pruebas de los dos servicios

Hay que ejecutar todo desde la carpeta raiz.

Ejecucion local

python3 -m venv venv/si1p1
source venv/si1p1/bin/activate
pip install -r requirements.txt

Luego, cada uno en una terminal (con el entorno activado):

python user.py
python file.py
python cliente.py

Ejecucion con Docker

docker compose up --build

Y en otra terminal, con el entorno activado:

python cliente.py

Para pararlo: Ctrl+C y docker compose down
