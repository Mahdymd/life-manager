"""utils/number_utils.py — فرمت اعداد و مبالغ."""


def format_currency(amount: float, symbol: str = "تومان") -> str:
    """123456789 → ۱۲۳,۴۵۶,۷۸۹ تومان"""
    formatted = f"{abs(amount):,.0f}"
    sign = "-" if amount < 0 else ""
    return f"{sign}{formatted} {symbol}"


def format_number(n: float, decimals: int = 0) -> str:
    if decimals:
        return f"{n:,.{decimals}f}"
    return f"{int(n):,}"


def to_persian_digits(text: str) -> str:
    mapping = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
    return text.translate(mapping)


def from_persian_digits(text: str) -> str:
    mapping = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
    return text.translate(mapping)


def clamp(value: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, value))
