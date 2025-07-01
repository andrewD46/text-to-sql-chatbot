# fastapi_app/openai_client.py
import os
import openai
from sqlalchemy import inspect
from database import engine

# --- OpenAI Configuration ---
api_key = os.getenv("OPENAI_API_KEY")
model_name = os.getenv("OPENAI_MODEL", "gpt-4-turbo")

if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set.")

client = openai.OpenAI(api_key=api_key)


def read_yaml_model(file_path: str) -> str:
    """
    Читает содержимое YAML файла и возвращает его в виде строки.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Ошибка: Файл семантической модели не найден по пути: {file_path}")
        return None
    except Exception as e:
        print(f"Произошла ошибка при чтении файла: {e}")
        return None


def get_db_schema_string() -> str:
    """
    Интроспектирует схему БД и возвращает её в виде строк CREATE TABLE.
    Это необходимо, чтобы LLM знала структуру таблиц.
    """
    inspector = inspect(engine)
    schema_str = ""
    for table_name in inspector.get_table_names():
        # Пропускаем системные таблицы Alembic, если вы их используете
        if table_name == 'alembic_version':
            continue

        columns = inspector.get_columns(table_name)
        schema_str += f"CREATE TABLE {table_name} (\n"
        for i, column in enumerate(columns):
            col_str = f"  {column['name']} {column['type']}"
            if i < len(columns) - 1:
                col_str += ","
            schema_str += col_str + "\n"
        schema_str += ");\n\n"
    return schema_str


async def generate_sql_from_question(question: str) -> str:
    """
    Отправляет запрос в OpenAI для генерации SQL из вопроса на естественном языке.
    """
    semantic_model_path = './semantic_model.yml'
    yaml_string = read_yaml_model(semantic_model_path)
    if not yaml_string:
        return "Ошибка: не удалось прочитать семантическую модель."

    system_prompt = f"""
    You are an expert PostgreSQL data analyst. Your task is to convert a user's question in natural language into a valid PostgreSQL query.
    You must only respond with the SQL query and nothing else. Do not add explanations, comments, or any surrounding text.
    The database has the following schema, defined by this semantic model:

    --- SEMANTIC MODEL START ---
    {yaml_string}
    --- SEMANTIC MODEL END ---

    - The query must be compatible with PostgreSQL.
    - Only use tables and columns defined in the semantic model above.
    - Use the relationships defined in the model to correctly join tables.
    - If the question cannot be answered with the given schema, respond with "I cannot answer this question."
    """

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        temperature=0.0,
        max_tokens=500,
    )
    sql_query = response.choices[0].message.content.strip()
    print(sql_query)

    # Очистка от возможных "```sql" и "```"
    if sql_query.startswith("```sql"):
        sql_query = sql_query[6:]
    if sql_query.endswith("```"):
        sql_query = sql_query[:-3]

    return sql_query.strip()
