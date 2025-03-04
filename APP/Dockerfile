# Dockerfile для FastAPI и Gradio приложения
FROM python:3.10-slim

# Установка зависимостей
WORKDIR /APP

# Скопируйте requirements.txt
COPY requirements.txt ./ 
RUN pip install --no-cache-dir -r requirements.txt

# Копируем приложение
COPY my_app_db.sql /docker-entrypoint-initdb.d/
COPY my_app_back.py ./
COPY my_app_front.py ./

# Установка переменной окружения для базы данных
ENV DATABASE_URL=postgresql://postgres:password@my_pg:5432/my_db

# Команда для запуска FastAPI
CMD ["uvicorn", "my_app_back:app", "--host", "0.0.0.0", "--port", "8000"]
