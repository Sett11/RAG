import uvicorn as uvicorn
from fastapi import FastAPI
from model import User

app = FastAPI()

user=User(name='John Doe',id=1)

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.get("/users")
def read_user(data=user):
    return {"name": user.name, 'id':user.id}

if __name__ == '__main__':
    uvicorn.run(app,host='127.0.0.1',port=8000)