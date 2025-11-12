"""Authentication API endpoints"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.features.auth.domain import UserCreate, UserResponse, UserLogin, Token
from app.features.auth.service import AuthService
from app.features.auth.api.dependencies import get_current_user
from app.shared.questionnaire.answer_handler import QuestionnaireAnswerHandler
from app.shared.questionnaire.repositories import QuestionnaireCompletionRepository
from app.shared.questionnaire.schemas import (
    QuestionnaireAnswersRequest,
    QuestionnaireAnswersResponse,
)
from app.shared.constants import QUESTIONNAIRE_IDS

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user with email and password

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        Created user

    Raises:
        HTTPException: If email already registered
    """
    auth_service = AuthService(db)

    try:
        user = auth_service.register_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login, get an access token for future requests

    Args:
        form_data: OAuth2 form with username (email) and password
        db: Database session

    Returns:
        Access token with onboarding completion status

    Raises:
        HTTPException: If credentials are incorrect
    """
    auth_service = AuthService(db)
    user = auth_service.authenticate(email=form_data.username, password=form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth_service.create_access_token(user)

    # Check onboarding completion status
    completion_repo = QuestionnaireCompletionRepository(db)
    onboarding_completed = completion_repo.is_completed(user.id, QUESTIONNAIRE_IDS["ONBOARDING"])

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "onboarding_completed": onboarding_completed,
        "user_id": user.id
    }


@router.post("/login/json", response_model=Token)
def login_json(user_login: UserLogin, db: Session = Depends(get_db)):
    """
    JSON login endpoint for clients that prefer JSON over form data

    Args:
        user_login: Login credentials
        db: Database session

    Returns:
        Access token with onboarding completion status

    Raises:
        HTTPException: If credentials are incorrect
    """
    auth_service = AuthService(db)
    user = auth_service.authenticate(email=user_login.email, password=user_login.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth_service.create_access_token(user)

    # Check onboarding completion status
    completion_repo = QuestionnaireCompletionRepository(db)
    onboarding_completed = completion_repo.is_completed(user.id, QUESTIONNAIRE_IDS["ONBOARDING"])

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "onboarding_completed": onboarding_completed,
        "user_id": user.id
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user = Depends(get_current_user)):
    """
    Get current user information

    Args:
        current_user: Current authenticated user

    Returns:
        User information
    """
    return current_user


@router.post("/test-token", response_model=UserResponse)
def test_token(current_user = Depends(get_current_user)):
    """
    Test access token validity

    Args:
        current_user: Current authenticated user

    Returns:
        User information if token is valid
    """
    return current_user


@router.post("/questionnaire/answers", response_model=QuestionnaireAnswersResponse, status_code=status.HTTP_200_OK)
def save_questionnaire_answers(
    request: QuestionnaireAnswersRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save or update questionnaire answers for the authenticated user.
    Supports partial submissions - only updates provided answers.

    Args:
        request: Questionnaire answers request containing questionnaire_id and answers
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message with questionnaire_id and answers count

    Raises:
        HTTPException: If there's an error saving answers

    Example request body:
    ```json
    {
        "questionnaire_id": "onboarding",
        "answers": {
            "name": "John Doe",
            "age": 30,
            "gender": "male",
            "conditions": ["73211009"],
            "which-type-of-diabetes": "type-2-diabetes",
            "what-is-your-diabetes-therapy": ["pills"],
            "notification-time": "19:00"
        }
    }
    ```
    """
    try:
        answer_handler = QuestionnaireAnswerHandler(db)
        answers_count, is_completed = answer_handler.save_answers(
            current_user.id,
            request.questionnaire_id,
            request.answers,
            mark_completed=request.completed
        )
        return QuestionnaireAnswersResponse(
            message="Questionnaire answers saved successfully",
            user_id=current_user.id,
            questionnaire_id=request.questionnaire_id,
            answers_count=answers_count,
            completed=is_completed
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving questionnaire answers: {str(e)}"
        )