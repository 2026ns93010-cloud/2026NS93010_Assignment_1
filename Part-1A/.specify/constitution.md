# Constitution

1. Python 3.11+ required for all implementation and tests.
2. All domain logic must use type hints and clear validation.
3. No use of eval(), exec(), pickle, or other unsafe dynamic execution.
4. Tasks are persisted in JSON using atomic file replacement.
5. Ruff check must return zero lint errors.
6. Bandit must report zero high or medium severity issues in src.
7. All task status transitions must be explicit and enforced.
