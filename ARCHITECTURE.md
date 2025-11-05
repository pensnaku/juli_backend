# Architecture Documentation

## Overview

This project follows a **feature-based modular architecture** that promotes:
- **Separation of Concerns** - Clear boundaries between layers
- **Testability** - Each layer can be tested independently
- **Maintainability** - Easy to locate and modify code
- **Scalability** - Simple to add new features without affecting existing ones

## Project Structure

```
app/
├── core/                    # Core functionality (shared across features)
│   ├── config.py           # Application configuration
│   ├── database.py         # Database connection and session management
│   ├── security.py         # Security utilities (JWT, password hashing)
│   └── deps.py             # Legacy dependencies (being phased out)
│
├── features/                # Feature modules (domain-driven design)
│   ├── auth/               # Authentication feature
│   │   ├── domain/         # Business entities and schemas
│   │   │   ├── models.py   # SQLAlchemy database models
│   │   │   └── schemas.py  # Pydantic request/response schemas
│   │   ├── repository/     # Data access layer
│   │   │   └── user_repository.py
│   │   ├── service/        # Business logic layer
│   │   │   └── auth_service.py
│   │   ├── api/            # API/Presentation layer
│   │   │   ├── router.py   # FastAPI endpoints
│   │   │   └── dependencies.py  # Route dependencies
│   │   └── tests/          # Feature-specific tests
│   │       ├── test_auth_service.py  # Unit tests
│   │       └── test_auth_api.py      # Integration tests
│   │
│   └── your_feature/              # YourModels feature (example CRUD)
│       ├── domain/
│       ├── repository/
│       ├── service/
│       ├── api/
│       └── tests/
│
├── shared/                  # Shared utilities across features
│   └── test_base.py        # Base test fixtures and utilities
│
├── api/                     # API composition layer
│   └── __init__.py         # Combines all feature routers
│
└── main.py                  # Application entry point
```

## Architectural Layers

### 1. Domain Layer (`domain/`)

**Purpose**: Contains business entities and data transfer objects

**Components**:
- `models.py` - SQLAlchemy ORM models (database tables)
- `schemas.py` - Pydantic models for validation and serialization

**Rules**:
- No dependencies on other layers
- Pure business logic only
- No HTTP or database concerns

**Example**:
```python
# domain/models.py
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
```

### 2. Repository Layer (`repository/`)

**Purpose**: Handles all database operations

**Responsibilities**:
- CRUD operations
- Database queries
- Data persistence

**Rules**:
- Only interacts with domain models
- No business logic
- Returns domain entities

**Example**:
```python
# repository/user_repository.py
class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()
```

### 3. Service Layer (`service/`)

**Purpose**: Contains business logic and orchestrates operations

**Responsibilities**:
- Business rules and validation
- Transaction management
- Coordinating multiple repositories
- Transforming data between layers

**Rules**:
- Uses repositories for data access
- No HTTP concerns
- Returns domain entities or raises exceptions

**Example**:
```python
# service/auth_service.py
class AuthService:
    def __init__(self, db: Session):
        self.repository = UserRepository(db)

    def register_user(self, user_data: UserCreate) -> User:
        if self.repository.exists_by_email(user_data.email):
            raise ValueError("Email already registered")
        # ... business logic
```

### 4. API Layer (`api/`)

**Purpose**: HTTP interface and request/response handling

**Components**:
- `router.py` - FastAPI routes and endpoints
- `dependencies.py` - Route-specific dependencies

**Responsibilities**:
- Request validation
- Response serialization
- HTTP status codes
- Error handling

**Rules**:
- Thin layer - delegates to services
- Handles HTTP concerns only
- Returns Pydantic schemas

**Example**:
```python
# api/router.py
@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return auth_service.register_user(user_data)
```

### 5. Tests Layer (`tests/`)

**Purpose**: Automated testing for the feature

**Test Types**:
- **Unit Tests** - Test services and repositories in isolation
- **Integration Tests** - Test API endpoints end-to-end

**Example**:
```python
# tests/test_auth_service.py
@pytest.mark.unit
def test_register_user_success(db: Session):
    auth_service = AuthService(db)
    user = auth_service.register_user(user_data)
    assert user.id is not None
```

## Data Flow

```
HTTP Request
    ↓
API Layer (router.py)
    ↓
Service Layer (business logic)
    ↓
Repository Layer (database operations)
    ↓
Database
    ↓
Repository Layer (returns domain models)
    ↓
Service Layer (processes and validates)
    ↓
API Layer (serializes to Pydantic schemas)
    ↓
HTTP Response
```

## Adding a New Feature

Follow these steps to add a new feature module:

### 1. Create Directory Structure

```bash
mkdir -p app/features/your_feature/{domain,repository,service,api,tests}
```

### 2. Define Domain Layer

Create `domain/models.py` and `domain/schemas.py`:

```python
# domain/models.py
from sqlalchemy import Column, Integer, String
from app.core.database import Base

class YourModel(Base):
    __tablename__ = "your_table"
    id = Column(Integer, primary_key=True)
    name = Column(String)
```

```python
# domain/schemas.py
from pydantic import BaseModel

class YourModelCreate(BaseModel):
    name: str

class YourModelResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
```

### 3. Create Repository

Create `repository/your_repository.py`:

```python
from sqlalchemy.orm import Session
from app.features.your_feature.domain.models import YourModel

class YourRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, name: str) -> YourModel:
        obj = YourModel(name=name)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj
```

### 4. Create Service

Create `service/your_service.py`:

```python
from sqlalchemy.orm import Session
from app.features.your_feature.repository.your_repository import YourRepository
from app.features.your_feature.domain.schemas import YourModelCreate

class YourService:
    def __init__(self, db: Session):
        self.repository = YourRepository(db)

    def create_item(self, data: YourModelCreate):
        return self.repository.create(data.name)
```

### 5. Create API Router

Create `api/router.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.features.your_feature.service.your_service import YourService
from app.features.your_feature.domain.schemas import YourModelCreate, YourModelResponse

router = APIRouter()

@router.post("/", response_model=YourModelResponse)
def create(data: YourModelCreate, db: Session = Depends(get_db)):
    service = YourService(db)
    return service.create_item(data)
```

### 6. Register Router

Add to `app/api/__init__.py`:

```python
from app.features.your_feature.api import router as your_feature_router

api_router_v1.include_router(
    your_feature_router,
    prefix="/your-feature",
    tags=["your-feature"]
)
```

### 7. Write Tests

Create tests in `tests/`:

```python
# tests/test_your_service.py
import pytest
from app.features.your_feature.service import YourService

@pytest.mark.unit
def test_create_item(db):
    service = YourService(db)
    # ... test logic
```

## Testing Strategy

### Unit Tests
- Test service logic in isolation
- Mock external dependencies
- Fast execution
- Located in `features/*/tests/test_*_service.py`

### Integration Tests
- Test API endpoints end-to-end
- Use test database
- Verify full request/response cycle
- Located in `features/*/tests/test_*_api.py`

### Running Tests

```bash
# Run all tests
pytest

# Run specific feature tests
pytest app/features/auth/tests/

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run with coverage
pytest --cov=app --cov-report=html
```

## Benefits of This Architecture

### 1. **Testability**
- Each layer can be tested independently
- Easy to mock dependencies
- Clear test boundaries

### 2. **Maintainability**
- Easy to locate code (feature-based organization)
- Changes are localized to specific layers
- Clear responsibility boundaries

### 3. **Scalability**
- Add new features without affecting existing ones
- Team members can work on different features independently
- Easy to extract features into microservices if needed

### 4. **Code Reusability**
- Services can be reused across different API endpoints
- Repositories can be shared across services
- Domain models are consistent throughout

### 5. **Dependency Management**
- Dependencies flow in one direction (API → Service → Repository → Domain)
- Easy to swap implementations (e.g., different databases)
- Loose coupling between layers

## Best Practices

1. **Keep layers thin** - Each layer should have a single responsibility
2. **Avoid circular dependencies** - Dependencies should flow downward only
3. **Use dependency injection** - Pass dependencies through constructors
4. **Write tests first** - TDD ensures testable design
5. **Keep domain models pure** - No framework dependencies in domain layer
6. **Use meaningful names** - Services should describe business operations
7. **Handle errors appropriately** - Services raise exceptions, API layer handles HTTP errors
8. **Document public APIs** - Add docstrings to all public methods

## Migration from Old Structure

The old flat structure has been reorganized:

```
Old Structure              →  New Structure
─────────────────────────     ─────────────────────────────────
app/models/user.py        →  app/features/auth/domain/models.py
app/schemas/user.py       →  app/features/auth/domain/schemas.py
app/services/auth_service →  app/features/auth/service/auth_service.py
app/api/v1/auth.py        →  app/features/auth/api/router.py
app/core/deps.py          →  app/features/auth/api/dependencies.py
```

The old structure files can be safely removed once you verify the new structure works correctly.