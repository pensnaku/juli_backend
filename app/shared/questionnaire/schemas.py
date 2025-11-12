"""Pydantic schemas for questionnaire-related requests and responses"""
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class QuestionnaireAnswersRequest(BaseModel):
    """Request schema for submitting questionnaire answers"""
    questionnaire_id: str = Field(..., description="ID of the questionnaire (e.g., 'onboarding', 'daily', 'biweekly')")
    answers: Dict[str, Any] = Field(..., description="Dictionary of question_id -> answer pairs")
    completed: bool = Field(default=False, description="Mark questionnaire as completed")

    class Config:
        json_schema_extra = {
            "example": {
                "questionnaire_id": "onboarding",
                "answers": {
                    "name": "John Doe",
                    "age": 30,
                    "gender": "male",
                    "conditions": ["73211009"],
                    "which-type-of-diabetes": "type-2-diabetes",
                    "notification-time": "19:00"
                },
                "completed": True
            }
        }


class QuestionnaireAnswersResponse(BaseModel):
    """Response schema for questionnaire answer submission"""
    message: str
    user_id: int
    questionnaire_id: str
    answers_count: int = Field(..., description="Number of answers processed")
    completed: bool = Field(..., description="Whether questionnaire was marked as completed")


class QuestionnaireCompletionResponse(BaseModel):
    """Response schema for questionnaire completion status"""
    questionnaire_id: str
    is_completed: bool
    assigned_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True