# Clarifications

1. Duplicate task ids are not allowed. The add operation raises ValueError when an id already exists.
2. Status transitions are strictly controlled with only three legal moves: TODO -> IN_PROGRESS, TODO -> DONE, IN_PROGRESS -> DONE.
3. Corrupted storage files are treated as empty state rather than fatal errors to allow recovery.
4. Priority ordering is HIGH > MEDIUM > LOW, and if priorities tie the title is used as a stable secondary sort.
