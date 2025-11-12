"""Pydantic models for questionnaire schema"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Any, Dict
from enum import Enum


class QuestionType(str, Enum):
    """Supported question types"""
    TEXT = "text"
    NUMBER = "number"
    SINGLE_CHOICE = "single_choice"
    MULTI_CHOICE = "multi_choice"
    TIME = "time"
    TIME_LIST = "time_list"
    BOOLEAN = "boolean"


class QuestionOption(BaseModel):
    """Option for choice-type questions"""
    value: str
    label: str
    system: Optional[str] = None  # e.g., "snomed" for medical codes


class ShowIfCondition(BaseModel):
    """Conditional display logic"""
    field: Optional[str] = None  # Field ID to check
    setting: Optional[str] = None  # Global setting to check
    equals: Optional[Any] = None  # Value must equal this
    contains: Optional[str] = None  # Value must contain this (for arrays)
    not_empty: Optional[bool] = None  # Value must not be empty


class QuestionValidation(BaseModel):
    """Validation rules for questions"""
    required: bool = False
    min: Optional[int] = None  # For numbers
    max: Optional[int] = None  # For numbers
    min_length: Optional[int] = None  # For text
    max_length: Optional[int] = None  # For text
    max_selections: Optional[int] = None  # For multi-choice
    min_times: Optional[int] = None  # For time_list
    max_times: Optional[int] = None  # For time_list
    pattern: Optional[str] = None  # Regex pattern


class Question(BaseModel):
    """Individual question definition"""
    id: str
    text: str
    type: QuestionType
    validation: Optional[QuestionValidation] = None
    help_text: Optional[str] = Field(None, alias="help_text")
    placeholder: Optional[str] = None
    show_if: Optional[ShowIfCondition] = Field(None, alias="show_if")
    options: Optional[List[QuestionOption]] = None
    allow_none: bool = False
    none_option: Optional[QuestionOption] = Field(None, alias="none_option")

    class Config:
        populate_by_name = True
        use_enum_values = True


class QuestionnaireSettings(BaseModel):
    """Global questionnaire settings"""
    ask_ethnicity: bool = False


class Questionnaire(BaseModel):
    """Complete questionnaire definition"""
    version: str
    questionnaire_id: str
    title: str
    description: Optional[str] = None
    settings: QuestionnaireSettings = QuestionnaireSettings()
    questions: List[Question]

    class Config:
        populate_by_name = True