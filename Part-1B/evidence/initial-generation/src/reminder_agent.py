from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

ALLOWED_INTENTS = {"CREATE", "RESCHEDULE", "SNOOZE", "CANCEL"}
UNSAFE_PATTERNS = [
    'ignore previous instructions',
    'override system prompt',
    'forget all previous rules',
    'reveal hidden instructions',
    'dump the prompt',
    'exfiltrate secrets',
]


def _normalize(text: str) -> str:
    return ' '.join(text.strip().lower().split())


def _parse_reference(reference: str | datetime) -> datetime:
    if isinstance(reference, datetime):
        return reference
    return datetime.fromisoformat(reference)


def _future_datetime(reference: datetime, text: str) -> datetime | None:
    lower = _normalize(text)
    if 'today' in lower:
        candidate = reference.replace(hour=9, minute=0, second=0, microsecond=0)
    elif 'tomorrow' in lower:
        candidate = (reference + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    elif 'next monday' in lower:
        days_until = (7 - reference.weekday()) % 7 or 7
        candidate = (reference + timedelta(days=days_until)).replace(hour=9, minute=0, second=0, microsecond=0)
    else:
        match = re.search(r'\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b', lower)
        if not match:
            return None
        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        period = match.group(3)
        if period == 'pm' and hour < 12:
            hour += 12
        if period == 'am' and hour == 12:
            hour = 0
        candidate = reference.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if candidate <= reference:
        candidate = candidate + timedelta(days=1)
    return candidate


def _extract_task_title(text: str) -> str | None:
    lower = _normalize(text)
    for keyword in ['remind me to', 'reminder to', 'remind me', 'create reminder', 'schedule', 'call', 'meeting', 'appointment', 'task']:
        if keyword in lower:
            start = lower.find(keyword)
            remainder = text[start + len(keyword):]
            remainder = remainder.replace(' tomorrow', '').replace(' today', '').replace(' at ', ' ')
            matched = re.sub(r'\b(\w+)?\s*(?:at|on|for|in)\b.*$', '', remainder)
            candidate = matched.strip(' ,:;.-')
            if candidate:
                return candidate.strip()
    candidate = re.sub(r'\b(create|cancel|reschedule|snooze|remind|set|schedule)\b', '', text, flags=re.IGNORECASE)
    candidate = candidate.strip(' ,:;.-')
    if candidate:
        return candidate
    return None


class ReminderAgent:
    def parse(self, user_input: str, reference_datetime: str | datetime) -> dict[str, Any]:
        reference = _parse_reference(reference_datetime)
        clean = user_input.strip()
        lowered = _normalize(clean)

        if any(pattern in lowered for pattern in UNSAFE_PATTERNS):
            return {
                'intent': 'CANCEL',
                'task_title': None,
                'scheduled_datetime_iso': None,
                'snooze_minutes': None,
                'needs_clarification': False,
                'clarification_question': None,
                'refusal_reason': 'Unsafe or adversarial prompt detected.',
                'confidence': 0.99,
            }

        intent = 'CREATE'
        if 'cancel' in lowered:
            intent = 'CANCEL'
        elif 'reschedule' in lowered or 'move' in lowered or 'change' in lowered:
            intent = 'RESCHEDULE'
        elif 'snooze' in lowered or 'delay' in lowered:
            intent = 'SNOOZE'

        task_title = _extract_task_title(clean)
        if not task_title and intent == 'CANCEL':
            task_title = 'unspecified task'

        scheduled_datetime = None
        snooze_minutes = None
        clarification_question = None
        needs_clarification = False

        if intent == 'SNOOZE':
            mins_match = re.search(r'(\d+)\s*(minute|minutes|min|mins|hour|hours|hr|hrs)', lowered)
            if mins_match:
                amount = int(mins_match.group(1))
                unit = mins_match.group(2)
                snooze_minutes = amount * 60 if 'hour' in unit else amount
            else:
                snooze_minutes = 15
            if not task_title:
                needs_clarification = True
                clarification_question = 'What reminder should I snooze?'

        if intent in {'CREATE', 'RESCHEDULE'} and not task_title:
            needs_clarification = True
            clarification_question = 'What reminder should I create or reschedule?'

        if intent in {'CREATE', 'RESCHEDULE'}:
            scheduled_datetime = _future_datetime(reference, clean)
            if scheduled_datetime is None:
                needs_clarification = True
                clarification_question = clarification_question or 'When should the reminder happen?'

        if needs_clarification:
            scheduled_datetime = None

        if scheduled_datetime is not None:
            scheduled_datetime_iso = scheduled_datetime.isoformat()
        else:
            scheduled_datetime_iso = None

        if intent == 'CANCEL' and task_title and not needs_clarification:
            scheduled_datetime_iso = None

        if not task_title and not needs_clarification and intent == 'CANCEL':
            needs_clarification = True
            clarification_question = 'Which task should I cancel?'

        confidence = 0.7
        if task_title and not needs_clarification:
            confidence += 0.15
        if scheduled_datetime_iso is not None:
            confidence += 0.1
        if intent == 'CANCEL' and not scheduled_datetime_iso:
            confidence += 0.05
        confidence = round(min(confidence, 0.99), 2)

        return {
            'intent': intent,
            'task_title': task_title,
            'scheduled_datetime_iso': scheduled_datetime_iso,
            'snooze_minutes': snooze_minutes,
            'needs_clarification': needs_clarification,
            'clarification_question': clarification_question,
            'refusal_reason': None,
            'confidence': confidence,
        }


def parse_reminder(user_input: str, reference_datetime: str | datetime) -> dict[str, Any]:
    return ReminderAgent().parse(user_input, reference_datetime)
