import streamlit as st

def main():
    st.title("Пример приложения на Streamlit")
    user_input = st.text_input("Введите текст:")

    if st.button("Отправить"):
        st.write(f"Вы ввели: {user_input}")

if __name__ == '__main__':
    main()