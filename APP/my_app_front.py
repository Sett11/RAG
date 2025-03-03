import gradio as gr
import requests

def insert_vector(vector):
    vector = [float(x) for x in vector.split(",")]
    response = requests.post("http://127.0.0.1:8000/insert_vector/", json={"vector": vector})
    
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
    return response.json()


def get_vectors():
    response = requests.get("http://127.0.0.1:8000/get_vectors/")
    return response.json()

def delete_vector(vector_id):
    response = requests.delete(f"http://127.0.0.1:8000/delete_vector/{vector_id}")
    return response.json()

with gr.Blocks() as app:
    gr.Markdown("## Vector Management API")
    
    with gr.Row():
        vector_input = gr.Textbox(label="Vector (comma separated)", placeholder="1.0,2.0,3.0")
        insert_btn = gr.Button("Insert Vector")
        output_insert = gr.Textbox(label="Insert Result")
        insert_btn.click(insert_vector, inputs=vector_input, outputs=output_insert)
    get_btn = gr.Button("Get Vectors")
    output_get = gr.Textbox(label="Vectors")
    get_btn.click(get_vectors, outputs=output_get)
    vector_id_input = gr.Textbox(label="Vector ID to Delete")
    delete_btn = gr.Button("Delete Vector")
    output_delete = gr.Textbox(label="Delete Result")
    delete_btn.click(delete_vector, inputs=vector_id_input, outputs=output_delete)

app.launch()