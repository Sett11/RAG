import gradio as gr
import requests
from itertools import cycle

def get_words(word='философия', quantity=10):
    # URL="http://127.0.0.1:8000/get_words/"
    URL="http://fastapi_app2:8000/get_words/"
    response = requests.get(URL, params={"word": word, "quantity": quantity})
    position=cycle(list(range(1,int(quantity)+1)))
    return '\n'.join([f'{str(next(position)).center(3)} {"→".center(3)} {search_word.ljust(len(search_word)+1)}' for search_word in response.json()['words']])

with gr.Blocks() as app:
    gr.Markdown("## ПОИСК СЛОВ ПОХОЖИХ ПО КОНТЕКСТУ")
    
    input_get_1 = gr.Textbox(label='введите слово', placeholder='философия')
    input_get_2 = gr.Textbox(label='введите количество желаемых похожих слов', placeholder='10')
    get_btn = gr.Button("получить слова")
    output_get = gr.Textbox(label="СЛОВА! (отсортированы по степени схожести)")
    get_btn.click(fn=get_words, inputs=(input_get_1, input_get_2), outputs=output_get)

app.launch(server_name="0.0.0.0", server_port=7860)