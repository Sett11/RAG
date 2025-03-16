from fastapi import FastAPI
import uvicorn
from model import get_model_output

app=FastAPI()

@app.get('/get_resp/')
def get_resp_model(input):
    return get_model_output(input)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)