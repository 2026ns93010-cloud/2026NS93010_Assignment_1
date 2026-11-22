# Plan

- Layer 1: CLI/API entrypoints in src/task_cli.py.
- Layer 2: Service logic in src/task_service.py with validation and state transitions.
- Layer 3: JSON persistence repository in src/task_store.py.
- Tests derive directly from AC-1..AC-8 and validate storage plus transitions.
