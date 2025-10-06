from datetime import date, datetime as _dt, timedelta
import re
from typing import Optional


def normalize_due_date(due: Optional[str]) -> Optional[str]:
    """Normalize natural-language dates to ISO YYYY-MM-DD.
    Examples: '7th october' -> '2025-10-07', 'today'/'tomorrow', '07-10' -> current-year.
    """
    if not due:
        return None

    d = due.strip().lower().replace(",", "")
    today = date.today()

    # Quick words
    if d == "today":
        return today.isoformat()
    if d == "tomorrow":
        return (today + timedelta(days=1)).isoformat()

    # Remove ordinal suffixes: 1st, 2nd, 3rd, 4th...
    d = re.sub(r"(\d{1,2})(st|nd|rd|th)\b", r"\1", d)

    months = {
        "jan": 1, "january": 1,
        "feb": 2, "february": 2,
        "mar": 3, "march": 3,
        "apr": 4, "april": 4,
        "may": 5,
        "jun": 6, "june": 6,
        "jul": 7, "july": 7,
        "aug": 8, "august": 8,
        "sep": 9, "sept": 9, "september": 9,
        "oct": 10, "october": 10,
        "nov": 11, "november": 11,
        "dec": 12, "december": 12,
    }

    # Patterns like "7 october [2025]" or "october 7 [2025]"
    parts = d.split()
    if len(parts) in (2, 3):
        if parts[0].isdigit() and parts[1] in months:
            day = int(parts[0])
            month = months[parts[1]]
            year = int(parts[2]) if len(parts) == 3 and parts[2].isdigit() else today.year
            try:
                return date(year, month, day).isoformat()
            except ValueError:
                pass
        if parts[0] in months and parts[1].isdigit():
            month = months[parts[0]]
            day = int(parts[1])
            year = int(parts[2]) if len(parts) == 3 and parts[2].isdigit() else today.year
            try:
                return date(year, month, day).isoformat()
            except ValueError:
                pass

    # Numeric: dd-mm[-yy|yyyy], dd/mm[/yy|yyyy], dd.mm[.yy|yyyy]
    m = re.match(r"^(\d{1,2})[-/.](\d{1,2})(?:[-/.](\d{2,4}))?$", d)
    if m:
        day, month, y = m.groups()
        day = int(day)
        month = int(month)
        if y is None:
            year = today.year
        else:
            year = int(y)
            if year < 100:
                year += 2000
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            pass

    # Already ISO
    try:
        return _dt.strptime(d, "%Y-%m-%d").date().isoformat()
    except ValueError:
        pass

    # Fallback: keep original text
    return due