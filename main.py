from transformers import pipeline
import gradio as gr


gpt = pipeline("text-generation", model="openai-community/gpt2")

def analyze_review(review):
    prompt = f"Анализируйте отзыв и определите, положительный он или отрицательный, а также выделите ключевые моменты:\nОтзыв: {review}\nАнализ:"
    response = gpt(prompt, max_length=200, num_return_sequences=1)[0]["generated_text"]
    return response

iface = gr.Interface(fn=analyze_review, inputs="text_area", outputs="text", title="Анализ отзывов с ChatGPT", description="Введите отзыв о продукте, и модель ChatGPT предоставит анализ.")

iface.launch()