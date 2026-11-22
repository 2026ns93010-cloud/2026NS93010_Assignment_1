# Clarifications

1. If a user omits the task title or action, the agent asks for clarification instead of guessing.
2. Relative phrases like tomorrow, next Friday, and 3pm are evaluated against the injected reference datetime.
3. Unsafe or adversarial requests are refused with a structured refusal_reason instead of continuing.
4. Snooze values are stored as minutes and are only valid if the task itself is already known.
