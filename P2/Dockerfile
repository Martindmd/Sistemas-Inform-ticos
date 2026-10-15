# Definimos la imagen base de python

FROM python:3.13.9

# Establecemos el directorio de trabajo del contenedor

WORKDIR /app

# Copia el archivo de dependencias para instalar las librerias necesarias de python

COPY requirements.txt requirements.txt

# Instala las dependencias de Python

RUN pip install --no-cache-dir -r requirements.txt

# Copia el código de la API dentro del contenedor

COPY . .

# Abre los puertos de escucha del contenedor

EXPOSE 5050 5051