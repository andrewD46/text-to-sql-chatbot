import os
from typing import Dict, Optional, Tuple

import pandas as pd
import streamlit as st
import requests  # Для выполнения HTTP-запросов
from dotenv import load_dotenv

# --- Конфигурация ---
load_dotenv()

# Используем переменную окружения для URL бэкенда, чтобы это работало в Docker
# Для локального запуска без Docker можно оставить "http://127.0.0.1:8000"
BACKEND_BASE_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")

# Эндпоинты API, которые нам теперь нужны
GENERATE_SQL_API_ENDPOINT = f"{BACKEND_BASE_URL}/api/generate_sql"
EXECUTE_SQL_API_ENDPOINT = f"{BACKEND_BASE_URL}/api/execute_sql"

API_TIMEOUT = 60  # Таймаут в секундах


def main():
    """Главная функция приложения."""
    st.set_page_config(page_title="AI SQL Аналитик", layout="wide")

    if "messages" not in st.session_state:
        reset_session_state()

    show_sidebar()
    display_chat_view()


# --- Функции для работы с API ---

def get_sql_from_backend(question: str) -> Tuple[Optional[Dict], Optional[str]]:
    """Получает сгенерированный SQL от бэкенда (OpenAI)."""
    # Так как бэкенд все еще может требовать имя пользователя, отправляем заглушку.
    request_body = {
        "question": question,
        "user_name": "default_user"
    }
    try:
        response = requests.post(GENERATE_SQL_API_ENDPOINT, json=request_body, timeout=API_TIMEOUT)
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to get response from AI backend: {e}"
        try:
            # Попытка извлечь более детальную ошибку от FastAPI
            error_detail = e.response.json().get('detail', str(e))
            error_msg = f"Error from AI backend: {error_detail}"
        except (ValueError, AttributeError):
            pass
        return None, error_msg


@st.cache_data(show_spinner=False)
def get_query_exec_result(query: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Выполняет SQL-запрос через бэкенд."""
    try:
        response = requests.post(EXECUTE_SQL_API_ENDPOINT, json={"sql_query": query})
        response.raise_for_status()
        data = response.json()
        if data.get("data") is not None:
            df = pd.DataFrame(data["data"])
            return df, None
        return None, data.get("error", "Unknown execution error")
    except requests.exceptions.RequestException as e:
        error_detail = str(e)
        try:
            error_detail = e.response.json().get('detail', str(e))
        except (ValueError, AttributeError):
            pass
        return None, error_detail


# --- Управление состоянием и отображением ---

def reset_session_state():
    """Сбрасывает состояние сессии чата."""
    st.session_state.messages = []


def show_sidebar():
    """Отображает боковую панель."""
    with st.sidebar:
        st.title('Меню')
        st.info("Это чат-бот для генерации SQL-запросов. Задайте свой вопрос в главном окне.")
        st.divider()
        if st.button("Начать новый чат", use_container_width=True, type="primary"):
            reset_session_state()
            st.rerun()


# --- Отображение основного интерфейса ---

def display_chat_view():
    """Отображает интерфейс чата."""
    st.title("🤖 AI SQL Аналитик")
    st.markdown("Задайте вопрос на естественном языке, и я попробую превратить его в SQL-запрос к вашей базе данных.")
    st.divider()

    # Отображаем текущий диалог
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sql" in message and message["sql"]:
                display_sql_and_results(
                    sql=message["sql"],
                    request_id=message["request_id"]
                )

    # Поле для ввода пользователя
    if prompt := st.chat_input("Какой у вас вопрос?"):
        # Добавляем сообщение пользователя в историю чата
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Получаем ответ от AI
        with st.chat_message("assistant"):
            with st.spinner("Думаю..."):
                response_data, error_msg = get_sql_from_backend(prompt)
                if error_msg:
                    response_content = f"К сожалению, произошла ошибка: {error_msg}"
                    st.error(response_content)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": response_content, "sql": None, "request_id": None})
                else:
                    sql_query = response_data['generated_sql']
                    request_id = response_data['request_id']
                    response_content = "✅ Вот SQL-запрос, который я сгенерировал:"
                    st.markdown(response_content)
                    display_sql_and_results(sql=sql_query, request_id=request_id)
                    # Сохраняем ответ ассистента в историю
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_content,
                        "sql": sql_query,
                        "request_id": request_id
                    })


def display_sql_and_results(sql: str, request_id: str):
    """Отображает SQL-запрос и результаты его выполнения."""
    with st.expander("Показать SQL-запрос", expanded=False):
        st.code(sql, language="sql")

    with st.expander("Результаты выполнения", expanded=True):
        with st.spinner("Выполняю SQL..."):
            df, err_msg = get_query_exec_result(sql)
            if err_msg:
                st.error(f"Не удалось выполнить SQL-запрос. Ошибка: {err_msg}")
            elif df is None or df.empty:
                st.info("Запрос не вернул данных.")
            else:
                data_tab, chart_tab = st.tabs(["Данные 📄", "График 📉"])
                with data_tab:
                    st.dataframe(df, use_container_width=True, height=300)
                with chart_tab:
                    display_charts_tab(df, request_id)


def display_charts_tab(df: pd.DataFrame, key_prefix: str):
    """Отображает вкладку с графиками."""
    if len(df.columns) < 2:
        st.info("Для построения графика необходимо как минимум 2 колонки.")
        return

    numerics = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
    # numeric_cols = df.select_dtypes(include=numerics).columns.tolist()

    # if not numeric_cols:
    #     st.warning("В данных нет числовых колонок для построения графика.")
    #     return

    col1, col2 = st.columns(2)
    x_col = col1.selectbox("Ось X", options=df.columns, key=f"x_col_{key_prefix}")
    y_col = col2.selectbox("Ось Y", options=df.columns, key=f"y_col_{key_prefix}")

    chart_type = st.selectbox(
        "Тип графика",
        options=["Линейный 📈", "Столбчатый 📊"],
        key=f"chart_type_{key_prefix}",
    )

    try:
        chart_df = df.set_index(x_col)
        if chart_type == "Линейный 📈":
            st.line_chart(chart_df[y_col])
        elif chart_type == "Столбчатый 📊":
            st.bar_chart(chart_df[y_col])
    except Exception as e:
        st.error(f"Не удалось построить график: {e}")


if __name__ == "__main__":
    main()