from fastapi import FastAPI
import redis
import psycopg2

app = FastAPI()

# Configuración para PostgreSQL
conn = psycopg2.connect(
    dbname="tu_db_name", user="tu_user", password="tu_password", host="localhost"
)

@app.get("/")
async def root():
    return {"message": "Hello from FastAPI!"}

@app.get("/songs")
async def get_songs():
    # Aquí conectas con Redis o PostgreSQL para obtener canciones
    return {"songs": ["song1", "song2"]}
