# Questionnaires

Simplified, non-FHIR questionnaire schema for Juli backend.

## Structure

```yaml
version: "1.0"
questionnaire_id: unique_id
title: Display Title
description: Optional description
settings:
  # Global settings that can be overridden
  ask_ethnicity: false

questions:
  - id: unique_question_id    # Must be unique, used by legacy system
    text: Question text
    type: text|number|single_choice|multi_choice|time|time_list|boolean
    validation:                # Optional
      required: true
      min: 0                   # For numbers
      max: 100
      min_length: 1            # For text
      max_length: 500
      max_selections: 2        # For multi_choice
    help_text: Optional help text
    show_if:                   # Optional conditional display
      field: other_question_id # Show if this field...
      equals: some_value       # ...equals this value
      contains: value          # ...contains this value (for arrays)
      not_empty: true          # ...is not empty
      setting: ask_ethnicity   # Or check a global setting
    options:                   # For choice questions
      - value: option_value
        label: Display Label
        system: snomed         # Optional: reference system
```

## Question Types

- **text**: Free text input
- **number**: Numeric input
- **single_choice**: Radio buttons / dropdown
- **multi_choice**: Checkboxes / multi-select
- **time**: Time picker
- **time_list**: Multiple time inputs
- **boolean**: Yes/No toggle

## Conditional Logic

Questions can be shown/hidden based on:
- **Field values**: `show_if: {field: "conditions", contains: "73211009"}`
- **Settings**: `show_if: {setting: "ask_ethnicity", equals: true}`
- **Empty check**: `show_if: {field: "conditions", not_empty: true}`

## Usage

```python
from app.shared.questionnaire import QuestionnaireService

service = QuestionnaireService()

# Load questionnaire
questionnaire = service.load_questionnaire("onboarding")

# Get frontend-friendly format
frontend_data = service.to_frontend_format(questionnaire)

# Filter questions based on context
visible = service.get_questions_for_context(
    questionnaire,
    context={"conditions": ["73211009"], "gender": "male"}
)
```

## Migration from FHIR

Key changes from FHIR schema:
- Removed verbose `Coding`, `system`, `display` nesting
- Simplified `enableWhen` → `show_if`
- Consolidated validation rules
- Kept original `linkId` as `id` for backward compatibility
- Removed unused FHIR metadata
- 90% size reduction

## Benefits

✅ **Simple**: Easy to read and write
✅ **Type-safe**: Pydantic validation
✅ **Flexible**: Conditional logic support
✅ **Lightweight**: ~70% smaller than FHIR
✅ **Frontend-friendly**: JSON-ready
✅ **Backward compatible**: Preserves original IDs