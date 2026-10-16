import math
from datetime import datetime


class ValidationError(ValueError):
    """Raised when a row or a table does not match the schema."""


def clean(value):
    # csv gives text. a missing value and a blank value are treated the same
    if value is None:
        return ""
    return value.strip()


def get_text(row, field, required=True):
    value = clean(row.get(field))
    if value == "":
        if required:
            raise ValidationError(f"{field} is required")
        return None
    return value


def get_id(row, field, required=True):
    value = get_text(row, field, required)
    if value is None:
        return None
    # "|" separates ids in tag lists and "::" is used in chunk ids later
    if " " in value or "|" in value or "::" in value:
        raise ValidationError(f"{field} '{value}' must not contain spaces, '|' or '::'")
    return value


def get_date(row, field, required=True):
    value = get_text(row, field, required)
    if value is None:
        return None
    try:
        # the length check stops short forms like 2026-1-5
        if len(value) != 10:
            raise ValueError
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError(f"{field} '{value}' is not a date in YYYY-MM-DD format") from None


def get_float(row, field, required=True, positive=False):
    """positive=True means the value must be above 0, otherwise 0 is allowed."""
    value = get_text(row, field, required)
    if value is None:
        return None
    try:
        number = float(value)
    except ValueError:
        raise ValidationError(f"{field} must be a number, got '{value}'") from None
    if not math.isfinite(number):
        raise ValidationError(f"{field} must be a normal number, got '{value}'")
    if positive and number <= 0:
        raise ValidationError(f"{field} must be greater than 0, got '{value}'")
    if number < 0:
        raise ValidationError(f"{field} must not be negative, got '{value}'")
    return number


def get_int(row, field):
    value = get_text(row, field)
    try:
        number = int(value)
    except ValueError:
        raise ValidationError(f"{field} must be a whole number, got '{value}'") from None
    if number < 0:
        raise ValidationError(f"{field} must not be negative, got '{value}'")
    return number


def get_choice(row, field, allowed):
    value = get_text(row, field).lower()
    if value not in allowed:
        raise ValidationError(f"{field} '{value}' must be one of: {', '.join(allowed)}")
    return value


def get_currency(row, field, required=True):
    value = get_text(row, field, required)
    if value is None:
        return None
    if len(value) != 3 or not value.isalpha() or not value.isupper():
        raise ValidationError(f"{field} '{value}' must be a 3 letter uppercase code like USD")
    return value


def get_bool(row, field):
    value = get_text(row, field).lower()
    if value not in ("true", "false"):
        raise ValidationError(f"{field} must be true or false, got '{value}'")
    return value == "true"


def get_id_list(row, field):
    """Ids separated by '|', for example P001|P002. Blank gives an empty tuple."""
    value = get_text(row, field, required=False)
    if value is None:
        return ()
    ids = []
    for part in value.split("|"):
        one_id = get_id({field: part}, field)
        if one_id in ids:
            raise ValidationError(f"{field} lists '{one_id}' twice")
        ids.append(one_id)
    return tuple(ids)
