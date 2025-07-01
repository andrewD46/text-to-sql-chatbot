import os
import requests
from typing import Dict, Optional, Tuple

import pandas as pd
import streamlit as st
from dotenv import load_dotenv


load_dotenv()


BACKEND_BASE_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")


GENERATE_SQL_API_ENDPOINT = f"{BACKEND_BASE_URL}/api/generate_sql"
EXECUTE_SQL_API_ENDPOINT = f"{BACKEND_BASE_URL}/api/execute_sql"

API_TIMEOUT = 60


def main():
    """Main function of Streamlit app."""
    st.set_page_config(page_title="Text-to-SQL Chatbot", layout="wide")

    if "messages" not in st.session_state:
        reset_session_state()

    show_sidebar()
    display_chat_view()


def get_sql_from_backend(question: str) -> Tuple[Optional[Dict], Optional[str]]:
    """Get generated SQL from backend."""
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
            error_detail = e.response.json().get('detail', str(e))
            error_msg = f"Error from AI backend: {error_detail}"
        except (ValueError, AttributeError):
            pass
        return None, error_msg


@st.cache_data(show_spinner=False)
def get_query_exec_result(query: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Run SQL query with via backend endpoint."""
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


def reset_session_state():
    """Reset session state."""
    st.session_state.messages = []


def show_sidebar():
    """Show sidebar on UI."""
    with st.sidebar:
        st.divider()
        if st.button("Начать новый чат", use_container_width=True, type="primary"):
            reset_session_state()
            st.rerun()

def display_chat_view():
    """Display main chat UI."""
    st.title("🤖 Text-to-SQL Chatbot")
    st.markdown("Ask a question in natural language and I'll try to turn it into an SQL query for your database.")
    st.divider()

    # show current messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sql" in message and message["sql"]:
                display_sql_and_results(
                    sql=message["sql"],
                    request_id=message["request_id"]
                )

    # input field
    if prompt := st.chat_input("What is your question?"):
        # add user message to a chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get answer from AI
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response_data, error_msg = get_sql_from_backend(prompt)
                if error_msg:
                    response_content = f"Sorry, an error occurred: {error_msg}"
                    st.error(response_content)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": response_content, "sql": None, "request_id": None})
                else:
                    sql_query = response_data['generated_sql']
                    request_id = response_data['request_id']
                    response_content = "✅ Here is the SQL query I generated:"
                    st.markdown(response_content)
                    display_sql_and_results(sql=sql_query, request_id=request_id)
                    # Save the assistant's response to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_content,
                        "sql": sql_query,
                        "request_id": request_id
                    })


def display_sql_and_results(sql: str, request_id: str):
    """Displays the SQL query and its execution results."""
    with st.expander("Show SQL Query", expanded=False):
        st.code(sql, language="sql")

    with st.expander("Execution Results", expanded=True):
        with st.spinner("Executing SQL..."):
            df, err_msg = get_query_exec_result(sql)
            if err_msg:
                st.error(f"Could not execute the SQL query. Error: {err_msg}")
            elif df is None or df.empty:
                st.info("The query returned no data.")
            else:
                data_tab, chart_tab = st.tabs(["Data 📄", "Chart 📉"])
                with data_tab:
                    st.dataframe(df, use_container_width=True, height=300)
                with chart_tab:
                    display_charts_tab(df, request_id)


def display_charts_tab(df: pd.DataFrame, key_prefix: str):
    """Displays the charts tab."""
    if len(df.columns) < 2:
        st.info("At least 2 columns are required to build a chart.")
        return

    col1, col2 = st.columns(2)
    x_col = col1.selectbox("X-axis", options=df.columns, key=f"x_col_{key_prefix}")
    y_col = col2.selectbox("Y-axis", options=df.columns, key=f"y_col_{key_prefix}")

    chart_type = st.selectbox(
        "Chart Type",
        options=["Line Chart 📈", "Bar Chart 📊"],
        key=f"chart_type_{key_prefix}",
    )

    try:
        chart_df = df.set_index(x_col)
        if chart_type == "Line Chart 📈":
            st.line_chart(chart_df[y_col])
        elif chart_type == "Bar Chart 📊":
            st.bar_chart(chart_df[y_col])
    except Exception as e:
        st.error(f"Could not build the chart: {e}")


if __name__ == "__main__":
    main()