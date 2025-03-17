from openai import OpenAI
from re import findall
from retrieval import search_valid_text

context="""Вы являетесь полезным ассистентом, который предоставляет информацию для решения важных задач, возможно очень значимых для науки.
Если Вам будет далее дана дополнительная информация, то используйте её для ответа в первую очередь. Если нет - то формируйте ответ
на общих основаниях. Всегда старайтесь давать развёрнутый ответ, если в запросе не указано другое.

"""
store=set(['скиба', 'адуло', 'колесников', 'косенков', 'лазаревич'])
messages=[{"role": "system","content": context}]

def get_philosoph_name(names):
    global messages
    messages[0]['content']+=f'Дополнительная информация: {search_valid_text(names)}\n'

def get_model_output(input):
    words=set(findall(r'\b[а-яa-z]+\b',input.lower()))
    names=[]
    for name in store:
        for word in words:
            if name in word or name[:-1] in word:
                names.append(name)
    if names:
        get_philosoph_name(names)
    client = OpenAI(
    api_key='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImU0YTJiZTkzLWZjMjYtNDlkZS05ZTUyLTQ3YjUwNjE4OTkzMCIsImlzRGV2ZWxvcGVyIjp0cnVlLCJpYXQiOjE3NDIwMjI3MDcsImV4cCI6MjA1NzU5ODcwN30.OVFkIPZOHRb7n81rEcpLz3qr6Vg4gHqCn6mWecMn8j4',
    base_url='https://bothub.chat/api/v2/openai/v1')
    
    messages.append({"role": "user", "content": input})
    stream = client.chat.completions.create(
        model="gpt-4.5-preview-2025-02-27",
        messages=messages,
        stream=True,)
    resp = ''
    for chunk in stream:
        part = chunk.to_dict()['choices'][0]['delta'].get('content', None)
        if part:
            resp += part
    messages.append({"role":"assistant","content":resp})
    return resp