"""Pydantic schemas for questionnaire-related requests and responses"""
from typing import Dict, Any, Optional, List
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


# ========== Daily Questionnaire Schemas ==========

class DailyAnswerRequest(BaseModel):
    """
    Request schema for submitting a single daily questionnaire answer.

    The 'answer' field supports both single values and multi-value answers:
    - Single value: answer = 4, answer = "good", answer = True
    - Multi-value: answer = {"mood": 4, "energy": 7}

    Multi-value answers are stored as separate observations with
    the variant field set to the dictionary key.
    """
    completion_date: str = Field(
        ...,
        description="Date in ISO format (YYYY-MM-DD)"
    )
    question_id: str = Field(
        ...,
        description="The question being answered"
    )
    answer: Any = Field(
        ...,
        description="The answer value (number, boolean, string, or dict for multi-value)"
    )
    questionnaire_id: str = Field(
        ...,
        description="Which questionnaire this belongs to (e.g., 'daily-asthma')"
    )
    completed: bool = Field(
        default=False,
        description="Set true when user finishes this questionnaire"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "completion_date": "2025-12-23",
                "question_id": "how-often-inhaler-or-nebulizer",
                "answer": 2,
                "questionnaire_id": "daily-asthma",
                "completed": False
            }
        }


class DailyAnswerResponse(BaseModel):
    """Response schema for daily answer submission"""
    message: str
    question_id: str
    questionnaire_id: str
    completed: bool = Field(..., description="Whether questionnaire was marked as completed")