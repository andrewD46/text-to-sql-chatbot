import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import FastAPI, Depends, HTTPException, status

from schemas import SQLGenerationRequest, SQLGenerationResponse, SQLExecutionRequest, SQLExecutionResponse

from openai_client import generate_sql_from_question
from database import get_db


app = FastAPI(
    title="Text-to-SQL Chatbot",
    description="A FastAPI application to generate SQL using different AI tools.",
    version="2.0.0",
)


def __execute_sql(db: Session, sql_query: str):
    try:
        result = db.execute(sql_query)
        if result.returns_rows:
            data = [dict(row) for row in result.mappings()]
            return {"data": data, "error": None}
        db.commit()
        return {"data": [{"status": "success", "rows_affected": result.rowcount}], "error": None}
    except Exception as e:
        db.rollback()
        return {"data": None, "error": str(e)}


@app.post("/api/generate_sql", response_model=SQLGenerationResponse, tags=["AI"])
async def generate_sql(
        request: SQLGenerationRequest
):
    """
    Generates a SQL query from a natural language question using OpenAI API.
    """
    try:
        # generate SQL with AI
        generated_sql = await generate_sql_from_question(request.question)

        if "I cannot answer this question." in generated_sql:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The question could not be answered based on the available database schema."
            )

        request_id = str(uuid.uuid4())

        return SQLGenerationResponse(
            request_id=request_id,
            user_question=request.question,
            generated_sql=generated_sql
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"An unexpected error occurred: {e}")


@app.post("/api/execute_sql", response_model=SQLExecutionResponse, tags=["SQL Execution"])
def execute_sql_endpoint(
        request: SQLExecutionRequest,
        db: Session = Depends(get_db)
):
    """Executes a given SQL query and returns the results."""
    result = __execute_sql(db, text(request.sql_query))
    if result["error"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    return result
