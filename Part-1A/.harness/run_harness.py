from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_gate(name: str, command: list[str]) -> dict[str, object]:
    start = datetime.utcnow().isoformat(timespec='seconds') + 'Z'
    try:
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        return {
            'name': name,
            'started_at': start,
            'returncode': completed.returncode,
            'stdout': completed.stdout,
            'stderr': completed.stderr,
            'passed': completed.returncode == 0,
        }
    except FileNotFoundError as exc:  # pragma: no cover
        return {
            'name': name,
            'started_at': start,
            'returncode': 127,
            'stdout': '',
            'stderr': str(exc),
            'passed': False,
        }


def main() -> int:
    gates = [
        run_gate('ruff', [sys.executable, '-m', 'ruff', 'check', 'src', 'tests']),
        run_gate('bandit', [sys.executable, '-m', 'bandit', '-r', 'src', '-ll']),
        run_gate('pytest', [sys.executable, '-m', 'pytest', 'tests', '-v']),
    ]
    result = {
        'timestamp': datetime.utcnow().isoformat(timespec='seconds') + 'Z',
        'overall_pass': all(gate['passed'] for gate in gates),
        'gates': gates,
    }

    evidence_dir = ROOT / 'evidence' / 'harness-results'
    evidence_dir.mkdir(parents=True, exist_ok=True)
    run_file = evidence_dir / f"run_{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}.json"
    run_file.write_text(json.dumps(result, indent=2), encoding='utf-8')

    print(json.dumps(result, indent=2))
    return 0 if result['overall_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
