# Resource Loader Usage

Simple utility for loading YAML and other resource files.

## Basic Usage

```python
from app.core.resource_loader import get_resource_loader

# Get the default loader instance
loader = get_resource_loader()

# Load a questionnaire
questionnaire = loader.load_questionnaire("onboarding_questionnaire")
print(questionnaire['resourceType'])  # "Questionnaire"
print(questionnaire['status'])  # "active"

# Access questionnaire items
for item in questionnaire['item']:
    print(f"Question: {item.get('text')}")
    print(f"Type: {item['type']}")
```

## Load Any YAML File

```python
# Load any YAML from resources directory
data = loader.load_yaml("questionnaires/onboarding_questionnaire.yml")

# Or create a custom loader with different base path
from app.core.resource_loader import ResourceLoader
from pathlib import Path

custom_loader = ResourceLoader(base_path=Path("/custom/path"))
```

## In a Service

```python
from app.core.resource_loader import get_resource_loader

class QuestionnaireService:
    def __init__(self):
        self.loader = get_resource_loader()

    def get_onboarding_questions(self):
        questionnaire = self.loader.load_questionnaire("onboarding_questionnaire")
        return questionnaire['item']

    def get_question_by_link_id(self, link_id: str):
        questionnaire = self.loader.load_questionnaire("onboarding_questionnaire")
        for item in questionnaire['item']:
            if item.get('linkId') == link_id:
                return item
        return None
```

## Get Resource Path

```python
# Get absolute path to a resource file
path = loader.get_resource_path("questionnaires/onboarding_questionnaire.yml")
print(path)  # /path/to/project/resources/questionnaires/onboarding_questionnaire.yml
```

## Error Handling

```python
try:
    questionnaire = loader.load_questionnaire("non_existent")
except FileNotFoundError as e:
    print(f"Questionnaire not found: {e}")
except yaml.YAMLError as e:
    print(f"Invalid YAML: {e}")
```
