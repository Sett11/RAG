import gradio as gr
import numpy as np
import plotly.express as px
import pandas as pd
import matplotlib.pyplot as plt

# def user_greeting(name):
#     return "Hi! " + name + " Welcome to your first Gradio application!😎"
    
# app =  gr.Interface(fn = user_greeting, inputs="text", outputs="text")
# app.launch()


# def blue_hue(input_img):
#     blue_hue_filter = np.array([
#             [0.272, 0.534, 0.131], 
#             [0.349, 0.686, 0.168],
#             [0.393, 0.769, 0.189]])
#     blue_hue_img = input_img.dot(blue_hue_filter.T)
#     blue_hue_img /= blue_hue_img.max()
#     return blue_hue_img

# demo = gr.Interface(blue_hue, gr.Image(width=300,height=200), "image")
# demo.launch()



# def plotly_plot():
#     x = ["Math", "Business", "Statistics", "IT", "Commerce"]
#     y = [68, 73, 82, 74, 85]
#     data = pd.DataFrame()
#     data['Subject'] = x
#     data['Score'] = y
#     p = px.bar(data, x='Subject', y='Score')
#     return p

# outputs = gr.Plot()

# demo = gr.Interface(fn=plotly_plot, inputs=None, outputs=outputs)

# demo.launch()



def plt_plot():
    x = ["Math", "Business", "Statistics", "IT", "Commerce"]
    y = [68, 73, 82, 74, 85]
    plt.rcParams['figure.figsize'] = 6,4
    fig = plt.figure()
    ax = fig.add_axes([0,0,1,1])
    ax.bar(x, y)
    plt.title("Marks per subject")
    plt.xlabel("Subject")
    plt.ylabel("Score")

    return fig

outputs = gr.Plot()

demo = gr.Interface(fn=plt_plot, inputs=None, outputs=outputs)

demo.launch()