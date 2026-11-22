from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import jsonschema
from pydantic import BaseModel, Field, ValidationError

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / 'src'
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from reminder_agent import ReminderAgent

SCHEMA = {
    'type': 'object',
    'properties': {
        'intent': {'type': 'string', 'enum': ['CREATE', 'RESCHEDULE', 'SNOOZE', 'CANCEL']},
        'task_title': {'type': ['string', 'null']},
        'scheduled_datetime_iso': {'type': ['string', 'null']},
        'snooze_minutes': {'type': ['integer', 'null']},
        'needs_clarification': {'type': 'boolean'},
        'clarification_question': {'type': ['string', 'null']},
        'refusal_reason': {'type': ['string', 'null']},
        'confidence': {'type': 'number', 'minimum': 0, 'maximum': 1},
    },
    'required': ['intent', 'task_title', 'scheduled_datetime_iso', 'snooze_minutes', 'needs_clarification', 'clarification_question', 'refusal_reason', 'confidence'],
    'additionalProperties': False,
}


class ReminderOutput(BaseModel):
    intent: str = Field(..., pattern='^(CREATE|RESCHEDULE|SNOOZE|CANCEL)$')
    task_title: str | None
    scheduled_datetime_iso: str | None
    snooze_minutes: int | None
    needs_clarification: bool
    clarification_question: str | None
    refusal_reason: str | None
    confidence: float = Field(..., ge=0, le=1)


def validate_schema(output: dict[str, Any]) -> tuple[bool, str]:
    try:
        jsonschema.validate(instance=output, schema=SCHEMA)
        ReminderOutput.model_validate(output)
        return True, 'schema valid'
    except (jsonschema.ValidationError, ValidationError) as exc:
        return False, str(exc)


def check_invariants(case: dict[str, Any], output: dict[str, Any]) -> tuple[bool, str]:
    if output.get('needs_clarification') is True:
        if not output.get('clarification_question'):
            return False, 'Clarification question empty when needs_clarification is true.'
        if output.get('scheduled_datetime_iso') is not None:
            return False, 'scheduled_datetime_iso must be null when clarification is needed.'
    if output.get('refusal_reason'):
        if case.get('category') != 'adversarial':
            return False, 'refusal_reason appeared on a non-adversarial case.'
    if output.get('scheduled_datetime_iso'):
        try:
            dt = datetime.fromisoformat(output['scheduled_datetime_iso'])
        except ValueError as exc:
            return False, str(exc)
        ref = datetime.fromisoformat(case['reference_datetime'])
        if dt <= ref:
            return False, 'scheduled_datetime_iso is not in the future.'
    if output.get('intent') not in {'CREATE', 'RESCHEDULE', 'SNOOZE', 'CANCEL'}:
        return False, 'Invalid intent.'
    if not (0 <= float(output.get('confidence', -1)) <= 1):
        return False, 'confidence must be between 0 and 1.'
    return True, 'invariants ok'


def semantic_score(output: dict[str, Any], ground_truth: str) -> float:
    actual = (output.get('task_title') or '').lower()
    truth = (ground_truth or '').lower()
    actual_tokens = set(re.findall(r'\w+', actual))
    truth_tokens = set(re.findall(r'\w+', truth))
    if not actual_tokens and not truth_tokens:
        return 1.0
    if not actual_tokens or not truth_tokens:
        return 0.0
    overlap = len(actual_tokens & truth_tokens)
    union = len(actual_tokens | truth_tokens)
    if union == 0:
        return 1.0
    return overlap / union


def property_pass(case: dict[str, Any], output: dict[str, Any], expression: str) -> bool:
    if expression == 'scheduled_datetime_iso in future':
        dt = output.get('scheduled_datetime_iso')
        if dt is None:
            return False
        return datetime.fromisoformat(dt) > datetime.fromisoformat(case['reference_datetime'])
    if expression.startswith('intent == '):
        expected = expression.split('==', 1)[1].strip().strip("'\"")
        return output.get('intent') == expected
    if expression.startswith('needs_clarification == '):
        expected = expression.split('==', 1)[1].strip().lower() == 'true'
        return output.get('needs_clarification') == expected
    if expression.startswith('clarification_question not empty'):
        return bool(output.get('clarification_question'))
    if expression.startswith('scheduled_datetime_iso == None'):
        return output.get('scheduled_datetime_iso') is None
    if expression.startswith('scheduled_datetime_iso not None'):
        return output.get('scheduled_datetime_iso') is not None
    if expression.startswith('refusal_reason not empty'):
        return bool(output.get('refusal_reason'))
    if expression.startswith('task_title contains '):
        expected = expression.split('contains', 1)[1].strip().lower()
        actual = (output.get('task_title') or '').lower()
        return expected in actual
    if expression.startswith('task_title not None'):
        return output.get('task_title') is not None
    if expression.startswith('intent in {'):
        allowed = {item.strip() for item in expression.split('{', 1)[1].split('}', 1)[0].split(',')}
        return output.get('intent') in allowed
    if expression.startswith('snooze_minutes == '):
        expected = int(expression.split('==', 1)[1].strip())
        return output.get('snooze_minutes') == expected
    return True


def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    output = ReminderAgent().parse(case['input_text'], case['reference_datetime'])
    schema_ok, schema_msg = validate_schema(output)
    invariant_ok, invariant_msg = check_invariants(case, output)
    property_ok = all(property_pass(case, output, expression) for expression in case.get('expected_properties', []))
    property_msg = 'properties ok' if property_ok else 'property mismatch'
    semantic = semantic_score(output, case['ground_truth_task'])
    case_score = 0.5 * (1.0 if schema_ok else 0.0) + 0.3 * (1.0 if invariant_ok else 0.0) + 0.2 * semantic
    if property_ok:
        case_score = min(1.0, case_score + 0.1)
    return {
        'case_id': case['id'],
        'category': case['category'],
        'schema_ok': schema_ok,
        'schema_msg': schema_msg,
        'invariant_ok': invariant_ok,
        'invariant_msg': invariant_msg,
        'property_ok': property_ok,
        'property_msg': property_msg,
        'semantic_score': round(semantic, 4),
        'case_score': round(case_score, 4),
        'output': output,
    }


def main() -> int:
    dataset = json.loads((ROOT / 'evals' / 'dataset.json').read_text(encoding='utf-8'))
    results = [evaluate_case(case) for case in dataset]
    aggregate = sum(item['case_score'] for item in results) / len(results) if results else 0.0
    failed = [item for item in results if not (item['schema_ok'] and item['invariant_ok'] and item['property_ok'])]
    pass_state = (aggregate >= 0.85) and all(item['schema_ok'] for item in results) and all(item['invariant_ok'] for item in results)
    report = {
        'timestamp': datetime.utcnow().isoformat(timespec='seconds') + 'Z',
        'threshold': 0.85,
        'aggregate_score': round(aggregate, 4),
        'overall_pass': pass_state,
        'case_results': results,
        'failed_cases': [item['case_id'] for item in failed],
    }
    out = ROOT / 'evidence'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'eval-results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if pass_state else 1


if __name__ == '__main__':
    raise SystemExit(main())
