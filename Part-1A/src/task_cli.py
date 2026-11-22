from __future__ import annotations

import argparse
import json
from pathlib import Path

from task_service import TaskService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Smart Todo CLI')
    parser.add_argument('--storage', default='tasks.json', help='Path to the JSON task store.')
    subparsers = parser.add_subparsers(dest='command', required=True)

    add_parser = subparsers.add_parser('add', help='Add a new task.')
    add_parser.add_argument('task_id')
    add_parser.add_argument('title')
    add_parser.add_argument('--description', default='')
    add_parser.add_argument('--status', default='TODO')
    add_parser.add_argument('--priority', default='MEDIUM')
    add_parser.add_argument('--tags', default='')

    list_parser = subparsers.add_parser('list', help='List tasks.')
    list_parser.add_argument('--tag', default=None)
    list_parser.add_argument('--status', default=None)

    update_parser = subparsers.add_parser('update-status', help='Update a task status.')
    update_parser.add_argument('task_id')
    update_parser.add_argument('status')

    delete_parser = subparsers.add_parser('delete', help='Delete a task.')
    delete_parser.add_argument('task_id')

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    service = TaskService(Path(args.storage))

    if args.command == 'add':
        tags = [tag.strip() for tag in args.tags.split(',') if tag.strip()]
        task = service.add_task(
            task_id=args.task_id,
            title=args.title,
            description=args.description,
            status=args.status,
            priority=args.priority,
            tags=tags,
        )
        print(json.dumps(task.to_dict(), indent=2))
        return

    if args.command == 'list':
        tasks = service.list_tasks(tag=args.tag, status=args.status)
        print(json.dumps([task.to_dict() for task in tasks], indent=2))
        return

    if args.command == 'update-status':
        task = service.update_status(args.task_id, args.status)
        print(json.dumps(task.to_dict(), indent=2))
        return

    if args.command == 'delete':
        service.delete_task(args.task_id)
        print(f'Deleted {args.task_id}')


if __name__ == '__main__':
    main()
