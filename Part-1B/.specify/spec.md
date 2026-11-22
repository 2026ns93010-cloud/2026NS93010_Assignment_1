# Natural-Language Reminder Agent Specification

## Output Schema
JSON fields include:
- intent: CREATE | RESCHEDULE | SNOOZE | CANCEL
- task_title: string | null
- scheduled_datetime_iso: ISO-8601 string | null
- snooze_minutes: integer | null
- needs_clarification: boolean
- clarification_question: string | null
- refusal_reason: string | null
- confidence: float between 0 and 1

## Invariants
INV-1: If needs_clarification == true, clarification_question must be non-empty and scheduled_datetime_iso must be null.
INV-2: If refusal_reason is present, the input request must be blocked or unsafe.
INV-3: scheduled_datetime_iso must be valid ISO-8601 and in the future relative to reference_datetime when not clarified.
INV-4: intent must be one of CREATE, RESCHEDULE, SNOOZE, CANCEL.
INV-5: confidence must be in [0,1].

## Evaluation Thresholds
Aggregate score must be at least 0.85. Layer 1 schema and safety guardrail checks must pass at 100%.
