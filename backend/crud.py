# fastapi_app/crud.py
import uuid
from sqlalchemy.orm import Session


# --- SQL Execution ---
def execute_sql(db: Session, sql_query: str):
    try:
        result = db.execute(sql_query)
        # Если это SELECT, возвращаем данные
        if result.returns_rows:
            data = [dict(row) for row in result.mappings()]
            return {"data": data, "error": None}
        # Для INSERT, UPDATE, DELETE и др.
        db.commit()
        return {"data": [{"status": "success", "rows_affected": result.rowcount}], "error": None}
    except Exception as e:
        db.rollback()
        return {"data": None, "error": str(e)}