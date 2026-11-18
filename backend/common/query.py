from django.utils.dateparse import parse_date
from rest_framework.exceptions import ValidationError

TRUE_VALUES = {"true", "1", "yes"}
FALSE_VALUES = {"false", "0", "no"}


def _raw(request, name):
    value = request.query_params.get(name)
    return None if value in (None, "") else value.strip()


def parse_bool_param(request, name):
    raw = _raw(request, name)
    if raw is None:
        return None
    lowered = raw.lower()
    if lowered in TRUE_VALUES:
        return True
    if lowered in FALSE_VALUES:
        return False
    raise ValidationError({name: "Must be true or false."})


def parse_int_param(request, name):
    raw = _raw(request, name)
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError as exc:
        raise ValidationError({name: "Must be a whole number."}) from exc


def parse_date_param(request, name):
    raw = _raw(request, name)
    if raw is None:
        return None
    try:
        parsed = parse_date(raw)
    except ValueError:
        parsed = None
    if parsed is None:
        raise ValidationError({name: "Must be a date in YYYY-MM-DD format."})
    return parsed
