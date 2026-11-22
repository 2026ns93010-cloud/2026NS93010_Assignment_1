# Smart Todo & Task CLI/API Specification

## Functional Requirements

FR-1: Users can add a task with an id, title, description, tags, priority, and status.
FR-2: Tasks are stored in a JSON file and loaded on startup.
FR-3: Each task supports the lifecycle TODO -> IN_PROGRESS -> DONE.
FR-4: A task may be listed, filtered by tag, and ordered by priority HIGH > MEDIUM > LOW.
FR-5: Invalid status transitions (including DONE -> TODO) are rejected.
FR-6: Corrupted or missing storage files are recovered to an empty task set without crashing.

## Schema

Each task record shall have:
- id: string
- title: string
- description: string
- status: TODO | IN_PROGRESS | DONE
- priority: HIGH | MEDIUM | LOW
- tags: list of strings

## Acceptance Criteria

AC-1: Adding a valid task with id "t1" writes the record to storage and returns the task.
AC-2: The task list is sorted as HIGH, MEDIUM, LOW when multiple tasks are present.
AC-3: A tag filter returns only tasks whose tags contain the requested tag.
AC-4: A status transition from TODO to IN_PROGRESS succeeds.
AC-5: A status transition from IN_PROGRESS to DONE succeeds.
AC-6: A direct transition from DONE to TODO raises a ValueError.
AC-7: An invalid priority value is rejected by validation.
AC-8: Invalid JSON data in storage is recovered to an empty list without crashing.
