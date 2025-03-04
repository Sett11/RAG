from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
import psycopg2
import os
import uvicorn

app=FastAPI()

DATABASE_URL=os.environ.get('DATABASE_URL','postgresql://postgres:password@localhost:5432/my_db')

def get_db_connection():
    conn=psycopg2.connect(DATABASE_URL)
    return conn

class VectorModel(BaseModel):
    vector: list[float]

class UpdateElementModel(BaseModel):
    value: float

@app.post("/insert_vector/")
async def insert_vector(vector_model: VectorModel):
    conn=get_db_connection()
    cursor=conn.cursor()
    cursor.execute(
        "INSERT INTO my_table (vector_column) VALUES (%s)",
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
    cursor.execute("SELECT * FROM my_table")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"vectors": rows}

@app.get("/get_vector/{id_vector}")
async def get_vector(id_vector: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT vector_column FROM my_table WHERE id = %s", (id_vector,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result is None:
        raise HTTPException(status_code=404, detail="Vector not found")
    return {"vector": result[0]}

@app.delete("/delete_vector/{vector_id}")
async def delete__vector(vector_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM my_table WHERE id = %s", (vector_id,))
    conn.commit()
    if cursor.rowcount == 0:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Vector not found")
    cursor.close()
    conn.close()
    return {"message": "Vector deleted successfully"}

@app.put("/update_vector_element/{vector_id}/{index}")
async def update_vector_element(vector_id: int, index: int, update_element: UpdateElementModel):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT vector_column FROM my_table WHERE id = %s", (vector_id,))
    result = cursor.fetchone()
    if result is None:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Vector not found")
    vector = result[0]
    if index < 0 or index >= len(vector):
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Index out of range")
    new_vector=vector[1:-1].split(',')
    new_vector[index]=str(update_element.value)
    vector=f"[{','.join(new_vector)}]"
    cursor.execute("UPDATE my_table SET vector_column = %s WHERE id = %s", (vector, vector_id))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Vector element updated successfully"}

@app.put("/update_vector/{vector_id}")
async def update_vector(vector_id: int, vector_model: VectorModel):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE my_table SET vector_column = %s WHERE id = %s", (vector_model.vector, vector_id))
    conn.commit()
    if cursor.rowcount == 0:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Vector not found")
    cursor.close()
    conn.close()
    return {"message": "Vector updated successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Invoke-WebRequest -Uri "http://127.0.0.1:8000/update_vector/3" -Method PUT -Headers @{"Content-Type"="application/json"} -Body '{"vector": [4.0, 5.0, 7.0]}'
# Invoke-WebRequest -Uri "http://127.0.0.1:8000/update_vector_element/3/1" -Method PUT -Headers @{"Content-Type"="application/json"} -Body '{"value": 5.5}'
# Invoke-WebRequest -Uri "http://127.0.0.1:8000/delete_vector/4" -Method DELETE
# Invoke-WebRequest -Uri "http://127.0.0.1:8000/insert_vector/" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"vector": [1.0, 2.0, 4.0]}'
# Invoke-WebRequest -Uri "http://127.0.0.1:8000/get_vectors/" -Method GET
# Invoke-WebRequest -Uri "http://127.0.0.1:8000/get_vector/3/" -Method GET