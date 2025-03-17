import gradio as gr
import requests

def get_resp_model_from_back(input):
    URL='http://127.0.0.1:8000/get_resp/'
    out=requests.get(URL,params={'input':input})
    return out.json()

with gr.Blocks() as app:
    gr.Markdown("## О ФИЛОСОФАХ И ИХ ФИЛОСОФИИ",elem_id="title")
    image_background = gr.Image(value="images\image_philosophy.png", type="pil", width='100', height='100', interactive=False, visible=True)

    input_get_1 = gr.Textbox(label='Изначально скажите, какой философ Вам интересен, а потом спросите меня о нём)',
                             placeholder='Пример: "ключевые аспекты понятия гармонии в работах Э.М. Сороко"')
    get_btn=gr.Button('попробуем..?')
    output_get = gr.Textbox(label='Извините, пожалуйста, за время ожидания - мне тоже нужно подумать)',
                            autoscroll=True,
                            show_copy_button=True,
                            max_lines=100,
                            placeholder='посмотрим ка...')

    with gr.Row():
        with gr.Column(scale=1):
            get_btn.click(fn=get_resp_model_from_back, inputs=input_get_1, outputs=output_get)
        with gr.Column(scale=1, min_width=200):
            input_get_1
            output_get
            image_background


app.launch(server_name="0.0.0.0", server_port=7860)
