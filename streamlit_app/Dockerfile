# 1. Используем официальный базовый образ Python
FROM python:3.10-slim

# 2. Устанавливаем рабочую директорию
WORKDIR /app

# 3. Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Копируем код приложения
COPY . .

# 5. Открываем порт, на котором работает Streamlit
EXPOSE 8501

# 6. Указываем команду для запуска
#    --server.address=0.0.0.0 нужен для доступа извне контейнера
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]