from __future__ import annotations

import json

import pytest

from src.task_service import TaskService


def test_ac_1_add_task_persists_and_returns_record(tmp_path):
    storage = tmp_path / 'tasks.json'
    service = TaskService(storage)
    task = service.add_task('t1', 'Draft plan', 'Write follow-up notes', priority='HIGH', tags=['work'])
    assert task.id == 't1'
    assert task.title == 'Draft plan'
    assert json.loads(storage.read_text(encoding='utf-8'))[0]['id'] == 't1'


def test_ac_2_tasks_sorted_by_priority(tmp_path):
    service = TaskService(tmp_path / 'tasks.json')
    service.add_task('low', 'Low task', priority='LOW')
    service.add_task('high', 'High task', priority='HIGH')
    service.add_task('medium', 'Medium task', priority='MEDIUM')
    ordered = [task.id for task in service.list_tasks()]
    assert ordered == ['high', 'medium', 'low']


def test_ac_3_tag_filter_matches_selected_tasks(tmp_path):
    service = TaskService(tmp_path / 'tasks.json')
    service.add_task('alpha', 'Alpha', tags=['work', 'urgent'])
    service.add_task('beta', 'Beta', tags=['home'])
    results = [task.id for task in service.list_tasks(tag='work')]
    assert results == ['alpha']


def test_ac_4_todo_to_in_progress_is_allowed(tmp_path):
    service = TaskService(tmp_path / 'tasks.json')
    service.add_task('todo-1', 'Progress task')
    updated = service.update_status('todo-1', 'IN_PROGRESS')
    assert updated.status == 'IN_PROGRESS'


def test_ac_5_in_progress_to_done_is_allowed(tmp_path):
    service = TaskService(tmp_path / 'tasks.json')
    service.add_task('todo-2', 'Complete task')
    service.update_status('todo-2', 'IN_PROGRESS')
    updated = service.update_status('todo-2', 'DONE')
    assert updated.status == 'DONE'


def test_ac_6_done_to_todo_is_rejected(tmp_path):
    service = TaskService(tmp_path / 'tasks.json')
    service.add_task('todo-3', 'Final task')
    service.update_status('todo-3', 'IN_PROGRESS')
    service.update_status('todo-3', 'DONE')
    with pytest.raises(ValueError):
        service.update_status('todo-3', 'TODO')


def test_ac_7_invalid_priority_is_rejected(tmp_path):
    service = TaskService(tmp_path / 'tasks.json')
    with pytest.raises(ValueError):
        service.add_task('bad', 'Bad priority', priority='URGENT')


def test_ac_8_corrupt_json_recovers_to_empty(tmp_path):
    storage = tmp_path / 'tasks.json'
    storage.write_text('{not valid json', encoding='utf-8')
    service = TaskService(storage)
    assert service.list_tasks() == []
