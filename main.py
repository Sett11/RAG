from fastapi import FastAPI
import uvicorn as uvi

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

if __name__=='__main__':
    uvi.run(app,host='127.0.0.1',port=8000)