Practica 2 - Sistemas Informaticos

user.py          -> servicio de usuarios (puerto 5050)
api.py           -> servicio principal del videoclub (puerto 5051)
client.py        -> pruebas de los dos servicios
schema.sql       -> tablas, triggers y procedimientos almacenados
populate.sql     -> datos iniciales
optimizacion.sql -> estudio con EXPLAIN de la consulta de /ventas/<año>/<país>

Hay que ejecutar todo desde la carpeta raiz.

Ejecucion con Docker

docker compose up --build

La primera vez la base de datos (PostgreSQL, usuario alumnodb, contraseña 1234, base de datos si1)
ejecuta sola schema.sql y populate.sql, y los datos se guardan en el volumen postgres_data.

Si con versiones nuevas de Docker falla con "pass --allow=network.host", construir las imagenes a mano
y levantar sin --build:

docker build --network host -t p2-user_api .
docker build --network host -t p2-api .
docker compose up

Y en otra terminal (solo necesita la libreria requests):

python client.py

Para pararlo: Ctrl+C y docker compose down
Para borrar tambien la base de datos y que se vuelva a crear desde cero: docker compose down -v

Optimizacion (una sola vez, con la base de datos recien creada):

docker compose exec -T db psql -U alumnodb -d si1 < optimizacion.sql

Consola de la base de datos:

docker compose exec db psql -U alumnodb -d si1

Ejecucion local (sin Docker para los servicios)

Hace falta la base de datos levantada con Docker (docker compose up db), que queda en localhost:5432.

python3 -m venv venv/si1p2
source venv/si1p2/bin/activate
pip install -r requirements.txt

Luego, cada uno en una terminal (con el entorno activado):

python user.py
python api.py
python client.py

Si falla por favor comprobad que la version de python del ordenador del laboratorio sea la misma que pone en Dockerfile,
ya que nos ha dado algunos problemas mientras comprobabamos en los ordenadores del laboratorio.
