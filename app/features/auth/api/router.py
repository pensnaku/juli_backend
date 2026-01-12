"""Authentication API endpoints"""
import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db

logger = logging.getLogger(__name__)
from app.features.auth.domain import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserWithOnboardingStatus,
    UserLogin,
    Token,
    EmailValidationRequest,
    EmailValidationResponse,
    UserReminderResponse,
    UserReminderUpdate,
    UserProfileUpdate,
    UserProfileResponse,
    UserConditionResponse,
)
from app.features.auth.service import AuthService
from app.features.auth.api.dependencies import get_current_user
from app.features.auth.repository import UserReminderRepository
from app.shared.questionnaire.answer_handler import QuestionnaireAnswerHandler
from app.shared.questionnaire.repositories import QuestionnaireCompletionRepository
from app.shared.questionnaire.schemas import (
    QuestionnaireAnswersRequest,
    QuestionnaireAnswersResponse,
)
from app.shared.constants import (
    QUESTIONNAIRE_IDS,
    WELLBEING_CONDITION_CODE,
    CONDITION_CODES,
    DAILY_ROUTINE_STUDENT,
)

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user with email and password, and automatically log them in

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        Access token with onboarding completion status (always false for new users)

    Raises:
        HTTPException: If email already registered
    """
    logger.info(f"Registration request received - email: {user_data.email}")

    auth_service = AuthService(db)

    try:
        user = auth_service.register_user(user_data)
        logger.info(f"User registered successfully - id: {user.id}, email: {user.email}")

        # Automatically log in the user by creating an access token
        access_token = auth_service.create_access_token(user)

        # Check onboarding completion status (will be false for new users)
        completion_repo = QuestionnaireCompletionRepository(db)
        onboarding_completed = completion_repo.is_completed(user.id, QUESTIONNAIRE_IDS["ONBOARDING"])

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "onboarding_completed": onboarding_completed,
            "user": user
        }
    except ValueError as e:
        logger.warning(f"Registration failed for {user_data.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/validate-email", response_model=EmailValidationResponse)
def validate_email(
    request: EmailValidationRequest,
    db: Session = Depends(get_db)
):
    """
    Validate email format and check if it's available for registration

    Args:
        request: Email validation request containing the email to validate
        db: Database session

    Returns:
        Validation result with:
        - is_valid: Whether the email format is valid
        - is_available: Whether the email is not already registered
        - message: Descriptive message about the validation result

    Example request body:
    ```json
    {
        "email": "user@example.com"
    }
    ```

    Example response:
    ```json
    {
        "email": "user@example.com",
        "is_valid": true,
        "is_available": true,
        "message": "This email address is available"
    }
    ```
    """
    auth_service = AuthService(db)
    validation_result = auth_service.validate_email(request.email)

    return EmailValidationResponse(
        email=request.email,
        **validation_result
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
        "user": user
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
        "user": user
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


@router.post("/test-token", response_model=UserWithOnboardingStatus)
def test_token(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Test access token validity and get user information with onboarding status

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        User information with onboarding completion status if token is valid
    """
    # Check onboarding completion status
    completion_repo = QuestionnaireCompletionRepository(db)
    onboarding_completed = completion_repo.is_completed(current_user.id, QUESTIONNAIRE_IDS["ONBOARDING"])

    # Convert user to dict and add onboarding status
    user_dict = {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "age": current_user.age,
        "gender": current_user.gender,
        "is_active": current_user.is_active,
        "is_superuser": current_user.is_superuser,
        "is_legacy_user": current_user.is_legacy_user,
        "terms_accepted": current_user.terms_accepted,
        "age_confirmed": current_user.age_confirmed,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
        "settings": current_user.settings,
        "conditions": current_user.conditions,
        "onboarding_completed": onboarding_completed
    }

    return user_dict


@router.patch("/profile", response_model=UserProfileResponse)
def update_user_profile(
    update_data: UserProfileUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the current user's profile information.

    Allows updating: full_name, age, gender, ethnicity, hispanic_latino, and fields on existing conditions.

    Args:
        update_data: User profile update data (all fields optional)
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated user profile information

    Example request body:
    ```json
    {
        "full_name": "Jane Smith",
        "age": 28,
        "gender": "female",
        "ethnicity": "asian",
        "conditions": [
            {
                "condition_code": "73211009",
                "diabetes_type": "type-2-diabetes",
                "therapy_type": "pills"
            }
        ]
    }
    ```
    """
    from app.features.auth.repository import UserRepository, UserConditionRepository
    from app.features.auth.domain import UserSettings

    user_repo = UserRepository(db)
    condition_repo = UserConditionRepository(db)
    user = user_repo.get_by_id(current_user.id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update only provided fields
    if update_data.full_name is not None:
        user.full_name = update_data.full_name
    if update_data.age is not None:
        user.age = update_data.age
    if update_data.gender is not None:
        user.gender = update_data.gender

    # Update ethnicity and hispanic_latino in user settings
    if update_data.ethnicity is not None or update_data.hispanic_latino is not None:
        if not user.settings:
            user.settings = UserSettings(user_id=user.id)
            db.add(user.settings)
        if update_data.ethnicity is not None:
            user.settings.ethnicity = update_data.ethnicity
        if update_data.hispanic_latino is not None:
            user.settings.hispanic_latino = update_data.hispanic_latino

    # Update fields on existing conditions
    if update_data.conditions is not None:
        for condition_data in update_data.conditions:
            condition = condition_repo.get_by_user_and_condition(user.id, condition_data.condition_code)
            if condition:
                if condition_data.diagnosed_by_physician is not None:
                    condition.diagnosed_by_physician = condition_data.diagnosed_by_physician
                if condition_data.duration is not None:
                    condition.duration = condition_data.duration
                if condition_data.physician_frequency is not None:
                    condition.physician_frequency = condition_data.physician_frequency
                if condition_data.diabetes_type is not None:
                    condition.diabetes_type = condition_data.diabetes_type
                if condition_data.therapy_type is not None:
                    condition.therapy_type = condition_data.therapy_type
                if condition_data.wants_glucose_reminders is not None:
                    condition.wants_glucose_reminders = condition_data.wants_glucose_reminders
                if condition_data.pain_type is not None:
                    condition.pain_type = condition_data.pain_type

    db.commit()
    db.refresh(user)

    return UserProfileResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        age=user.age,
        gender=user.gender,
        ethnicity=user.settings.ethnicity if user.settings else None,
        hispanic_latino=user.settings.hispanic_latino if user.settings else None
    )


@router.post("/conditions", response_model=UserConditionResponse, status_code=status.HTTP_201_CREATED)
def create_condition(
    condition_code: str = Query(..., description="SNOMED condition code (e.g., '73211009' for Diabetes)"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new condition for the current user.

    Args:
        condition_code: SNOMED code for the condition (pass as query param: ?condition_code=73211009)
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created condition

    Raises:
        HTTPException: If condition code is invalid or condition already exists
    """
    from app.features.auth.repository import UserConditionRepository
    from app.features.auth.domain.schemas import UserConditionCreate

    logger.info(f"create_condition called with condition_code: {condition_code}")
    logger.info(f"current_user.id: {current_user.id}")

    condition_repo = UserConditionRepository(db)

    # Validate condition code
    if condition_code not in CONDITION_CODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid condition code: {condition_code}"
        )

    # Check if condition already exists
    existing = condition_repo.get_by_user_and_condition(current_user.id, condition_code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Condition already exists for this user"
        )

    # Create the condition
    condition_info = CONDITION_CODES[condition_code]
    condition_data = UserConditionCreate(
        condition_code=condition_code,
        condition_label=condition_info["label"],
        condition_system=condition_info["system"],
    )
    condition = condition_repo.create(current_user.id, condition_data)

    return condition


@router.delete("/conditions/{condition_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_condition(
    condition_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a condition by ID.

    All users must always have at least one condition. If a non-student user tries
    to delete their last condition, an error is returned. Students can delete their
    last condition, but it will automatically be replaced with the Wellbeing condition.

    Args:
        condition_id: ID of the condition to delete
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException: If condition not found, doesn't belong to user, or is the last
                      condition for a non-student user
    """
    from app.features.auth.repository import UserConditionRepository
    from app.features.auth.domain.schemas import UserConditionCreate

    condition_repo = UserConditionRepository(db)
    condition = condition_repo.get_by_id(condition_id)

    if not condition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Condition not found"
        )

    if condition.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this condition"
        )

    # Check if this is the last condition
    user_conditions = condition_repo.get_by_user_id(current_user.id)
    is_last_condition = len(user_conditions) == 1

    if is_last_condition:
        # Check if user is a student
        is_student = (
            current_user.settings
            and current_user.settings.daily_routine == DAILY_ROUTINE_STUDENT
        )

        if not is_student:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your last condition. All users must have at least one condition."
            )

        # Student trying to delete last condition
        # If it's already Wellbeing, they can't delete it
        if condition.condition_code == WELLBEING_CONDITION_CODE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete Wellbeing condition. All users must have at least one condition."
            )

        # Student deleting last non-Wellbeing condition - replace with Wellbeing
        condition_repo.delete(condition)

        # Create Wellbeing condition
        wellbeing_info = CONDITION_CODES[WELLBEING_CONDITION_CODE]
        wellbeing_condition = UserConditionCreate(
            condition_code=WELLBEING_CONDITION_CODE,
            condition_label=wellbeing_info["label"],
            condition_system=wellbeing_info["system"],
        )
        condition_repo.create(current_user.id, wellbeing_condition)
    else:
        condition_repo.delete(condition)

    return None


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


@router.get("/reminders", response_model=List[UserReminderResponse])
def get_reminders(
    reminder_type: Optional[str] = Query(
        default=None,
        description="Filter by reminder type (e.g., 'daily_check_in', 'medication_reminder')"
    ),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all reminders for the current user, optionally filtered by type.

    Args:
        reminder_type: Optional filter by reminder type
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of user reminders
    """
    repo = UserReminderRepository(db)

    if reminder_type:
        reminders = repo.get_by_user_and_type(current_user.id, reminder_type)
    else:
        reminders = repo.get_by_user_id(current_user.id)

    return reminders


@router.put("/reminders/{reminder_id}", response_model=UserReminderResponse)
def update_reminder(
    reminder_id: int,
    update_data: UserReminderUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update a reminder's time or active status.

    Args:
        reminder_id: ID of the reminder to update
        update_data: Fields to update (time, is_active)
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated reminder

    Raises:
        HTTPException: If reminder not found or doesn't belong to user
    """
    repo = UserReminderRepository(db)
    reminder = repo.get_by_id(reminder_id)

    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )

    if reminder.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this reminder"
        )

    updated_reminder = repo.update(reminder, update_data)
    return updated_reminder