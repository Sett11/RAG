import uvicorn as uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse

app = FastAPI()

sample_product_1 = {
    "product_id": 123,
    "name": "Smartphone",
    "category": "Electronics",
    "price": 599.99
}

sample_product_2 = {
    "product_id": 456,
    "name": "Phone Case",
    "category": "Accessories",
    "price": 19.99
}

sample_product_3 = {
    "product_id": 789,
    "name": "Iphone",
    "category": "Electronics",
    "price": 1299.99
}

sample_product_4 = {
    "product_id": 101,
    "name": "Headphones",
    "category": "Accessories",
    "price": 99.99
}

sample_product_5 = {
    "product_id": 202,
    "name": "Smartwatch",
    "category": "Electronics",
    "price": 299.99
}

sample_products = [sample_product_1, sample_product_2, sample_product_3, sample_product_4, sample_product_5]

@app.get('/',response_class=FileResponse)
def root():
    return 'index.html'

@app.get('/product/{product_id}')
def get_product(product_id:int):
    try:
        return next(i for i in sample_products if i['product_id']==product_id)
    except:
        return {'message':'Product not found'}

@app.get('/products/search')
def product_search(keyword:str,category:str,limit:int):
    return [i for i in sample_products if keyword in i['name'] and i['category']==category][:limit]

if __name__=='__main__':
    uvicorn.run(app,host='127.0.0.1',port=8000)