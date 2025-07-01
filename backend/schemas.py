from typing import List, Optional

from pydantic import BaseModel, Field


class StatusResponse(BaseModel):
    status: str
    message: str

class SQLGenerationRequest(BaseModel):
    question: str = Field(..., description="Natural language question from the user.")
    user_name: str = Field(..., description="The user asking the question.")

class SQLGenerationResponse(BaseModel):
    request_id: str
    user_question: str
    generated_sql: str
    warnings: List[str] = []

class SQLExecutionRequest(BaseModel):
    sql_query: str

class SQLExecutionResponse(BaseModel):
    data: Optional[list] = None
    error: Optional[str] = None