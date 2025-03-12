import gradio as gr
import requests


def get_words(word,quantity):
    response = requests.get("http://127.0.0.1:8000/get_words/")
    return response.json()


with gr.Blocks() as app:
    gr.Markdown("## WORDS Management API")
    get_btn = gr.Button("Get Words")
    input_get_1=gr.Textbox('Insert word',placeholder='Your word')
    input_get_2=gr.Textbox('Insert your quantity')
    output_get = gr.Textbox(label="Words")
    get_btn.click(get_words,inputs=(input_get_1,input_get_2),outputs=output_get)

app.launch(server_name="0.0.0.0", server_port=7860)