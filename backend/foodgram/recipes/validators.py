import re

from django.core.exceptions import ValidationError

LIMIT: int = 1


def validation_slug(slug: str) -> None:
    """Проверка правильности наименование slug тега"""
    pattern = re.compile(r'^[-a-zA-Z0-9_]+$')
    if not pattern.match(slug):
        raise ValidationError(
            'Не правильное значение slug'
        )


def validation_cooking_time(int_time: int) -> None:
    """Проверка времени приготовления"""
    if int_time < LIMIT:
        raise ValidationError(
            'Время приготовление не может быть меньше 1 минуты'
        )


def validation_amount_ingredients(int_ingredients: int) -> None:
    """Проверка количества ингридиентов"""
    if int_ingredients < LIMIT:
        raise ValidationError(
            'Минимальное количество ингридиентов 1'
        )
