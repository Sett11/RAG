from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
import psycopg2
import os
import uvicorn 

app=FastAPI()

# DATABASE_URL = os.environ.get('DATABASE_URL','postgresql://postgres:password@localhost:5432/my_db')
DATABASE_URL = os.environ.get('DATABASE_URL','postgresql://postgres:password@my_pgv_app:5432/my_emb_db')

def get_db_connection():
    conn=psycopg2.connect(DATABASE_URL)
    return conn

class VectorModel(BaseModel):
    sentence: str

@app.get("/get_words/")
async def get_words():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM word_emb")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"words": rows}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)