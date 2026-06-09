"""Вспомогательные функции для валидации и форматирования"""

import re
from datetime import datetime


def validate_name(name):
    """Проверяет, что имя/фамилия содержит только буквы, дефис и пробел."""
    return bool(re.fullmatch(r"[A-Za-zА-Яа-яЁё\- ]+", name.strip()))


def validate_phone(phone):
    """Проверяет формат телефона."""
    # Разрешаем цифры, пробелы, дефисы, скобки, плюс. Длина от 10 до 15 знаков.
    return bool(re.match(r"^[\+\d\s\-\(\)]{10,15}$", phone))


def validate_email(email):
    """Проверяет формат email."""
    return bool(re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email))


def format_datetime(dt_str):
    """Преобразует строку даты из БД в формат ДД.ММ.ГГГГ ЧЧ:ММ."""
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d.%m.%Y %H:%M")
    except:
        return dt_str


def format_date_only(dt_str):
    """Преобразует строку даты в формат ДД.ММ.ГГГГ."""
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d.%m.%Y")
    except:
        return dt_str