# Dockerfile для FastAPI и Gradio приложения
FROM python:3.10-slim

# Установка зависимостей
WORKDIR /APP_2

# Скопируйте requirements.txt
COPY requirements.txt ./ 
RUN pip install --no-cache-dir -r requirements.txt

# Копируем приложение
COPY app2_db.sql /docker-entrypoint-initdb.d/
COPY app2_back.py ./
COPY app2_front.py ./

# Установка переменной окружения для базы данных
ENV DATABASE_URL=postgresql://postgres:password@pgv_emb_app:5432/my_emb_db

# Команда для запуска FastAPI
CMD ["uvicorn", "app2_back:app", "--host", "0.0.0.0", "--port", "8000"]