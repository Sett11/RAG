from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import os
import uvicorn
import numpy as np
import faiss
import ast

app = FastAPI()

# DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:password@pgv_emb_app:5432/my_emb_db') # for launch through Docker 
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/my_emb_db')

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def get_vector_for_word(word: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT embedding FROM word_emb WHERE word = %s", (word,))
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if result is None:
        raise HTTPException(status_code=404, detail="Word not found in database")

    vector = np.array(ast.literal_eval(result[0])).astype('float32')
    return vector

@app.get("/get_words/")
async def get_words(word: str, quantity: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    word_vector = get_vector_for_word(word)

    cursor.execute("SELECT word, embedding FROM word_emb")
    rows = cursor.fetchall()

    embeddings = np.array([ast.literal_eval(row[1]) for row in rows]).astype('float32')
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    k = quantity + 1
    D, I = index.search(np.array([word_vector]), k)  # Ищем k ближайших

    similar_words = [rows[i][0] for i in I[0]]

    cursor.close()
    conn.close()

    return {"words": similar_words[1:]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)