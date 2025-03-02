from fastapi import FastAPI
from pydantic import BaseModel
import psycopg2
import os

app = FastAPI()

# Подключение к базе данных PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:1111@localhost:5432/my_db')

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

class VectorModel(BaseModel):
    vector: list[float]

@app.post("/insert_vector/")
async def insert_vector(vector_model: VectorModel):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Вставка в таблицу с вектором
    cursor.execute(
        "INSERT INTO your_table (vector_column) VALUES (%s)",
        (vector_model.vector,)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Vector inserted successfully"}

@app.get("/get_vectors/")
async def get_vectors():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM your_table")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return {"vectors": rows}
