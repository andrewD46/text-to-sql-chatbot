import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import FastAPI, Depends, HTTPException, status

from crud import execute_sql
from schemas import SQLGenerationRequest, SQLGenerationResponse, SQLExecutionRequest, SQLExecutionResponse, StatusResponse

from openai_client import generate_sql_from_question
from database import get_db


app = FastAPI(
    title="Postgres + OpenAI Analyst API",
    description="A FastAPI application to generate SQL using OpenAI and manage query history in PostgreSQL.",
    version="2.0.0",
)


# --- API Endpoints ---

@app.post("/api/generate_sql", response_model=SQLGenerationResponse, tags=["AI"])
async def generate_sql(
        request: SQLGenerationRequest,
        db: Session = Depends(get_db)
):
    """
    Generates a SQL query from a natural language question using OpenAI API.
    """
    try:
        # 2. Генерируем SQL через OpenAI
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
    result = execute_sql(db, text(request.sql_query))
    if result["error"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    return result
