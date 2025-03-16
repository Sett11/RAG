from openai import OpenAI

context='You are a helpful assistant that provides information'
messages=[{"role":"system","content":context}]

def get_model_output(input):
    client = OpenAI(
    api_key='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImU0YTJiZTkzLWZjMjYtNDlkZS05ZTUyLTQ3YjUwNjE4OTkzMCIsImlzRGV2ZWxvcGVyIjp0cnVlLCJpYXQiOjE3NDIwMjI3MDcsImV4cCI6MjA1NzU5ODcwN30.OVFkIPZOHRb7n81rEcpLz3qr6Vg4gHqCn6mWecMn8j4',
    base_url='https://bothub.chat/api/v2/openai/v1'
    )
    
    messages.append({"role": "user", "content": input})
    stream = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        stream=True,
    )
    resp = ''
    for chunk in stream:
        part = chunk.to_dict()['choices'][0]['delta'].get('content', None)
        if part:
            resp += part
    messages.append({"role":"assistant","content":resp})
    return resp