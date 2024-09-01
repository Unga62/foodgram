import csv

from django.core.management.base import BaseCommand
from recipes.models import Ingredients


class Command(BaseCommand):
    help = "Loads ingredients from csv"

    def handle(self, *args, **kwargs):
        with open(
            'recipes/data/ingredients.csv',
            'r',
            encoding='utf-8'
        ) as file:
            ingredients = csv.reader(file, delimiter=',')
            for ingredient in ingredients:
                if len(ingredient) == 2:
                    Ingredients.objects.get_or_create(
                        name=ingredient[0],
                        measurement_unit=ingredient[1]
                    )

        self.stdout.write(self.style.SUCCESS('База данных успешно заполнена'))
        return 'OK'
