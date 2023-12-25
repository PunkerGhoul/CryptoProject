import os
from dotenv import load_dotenv
from mysql.connector import connect, Error


# Cargar variables de entorno desde el archivo .env
load_dotenv()

def conectar():
    return connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_DATABASE", "chatsecure_db")
    )

def gen_cursor(conexion: connect):
    return conexion.cursor()