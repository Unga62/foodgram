from random import choices

from api.const import (
    CHARACTERS,
    MEASUREMENT_UNIT_MAX_LENGTH,
    NAME_ING_MAX_LENGTH,
    RECIPES_NAME_MAX_LENGTH,
    SHORT_LINK_DB,
    TAGS_AND_SLUG_MAX_LENGTH,
)
from django.contrib.auth import get_user_model
from django.db import models
from recipes.validators import (
    validation_amount_ingredients,
    validation_cooking_time,
    validation_slug,
)

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        max_length=TAGS_AND_SLUG_MAX_LENGTH,
        verbose_name='Тег'
    )
    slug = models.CharField(
        max_length=TAGS_AND_SLUG_MAX_LENGTH,
        validators=(validation_slug,)
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=NAME_ING_MAX_LENGTH,
        verbose_name='Ингредиент'
    )
    measurement_unit = models.CharField(
        max_length=MEASUREMENT_UNIT_MAX_LENGTH,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        related_name='recipes'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='ArrayIngredient',
        verbose_name='Ингредиенты',
    )
    name = models.CharField(
        max_length=RECIPES_NAME_MAX_LENGTH,
        verbose_name='Наименование рецепта',
    )
    image = models.ImageField(
        upload_to='recipes/image/',
        verbose_name='Изображение рецепта',
        null=True,
        default=None,
        blank=True,
    )
    text = models.TextField(verbose_name='Описание рецепта')
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления',
        validators=(validation_cooking_time,)
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class ArrayIngredient(models.Model):
    recipes = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='array_ingredients',
    )
    ingredients = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='array_ingredients',
    )
    amount = models.PositiveIntegerField(
        validators=(validation_amount_ingredients,),
        verbose_name='Количество ингредиентов',
    )

    class Meta:
        verbose_name = 'Количество ингредиентов'
        verbose_name_plural = 'Количество ингредиентов'
        constraints = (
            models.UniqueConstraint(
                fields=('recipes', 'ingredients'),
                name='Unique recipes in ingredients'
            ),
        )

    def __str__(self):
        return (f'В рецепте {self.recipes} количество '
                f'ингредиентов {self.ingredients}-{self.amount}')


class BaseFavoritesandShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        null=True,
    )
    recipes = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        null=True,
    )

    class Meta:
        abstract = True


class Favorite(BaseFavoritesandShoppingCart):

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipes'),
                name='Unique recipes in favorites'
            ),
        )

    def __str__(self):
        return f'Пользователь {self.user} добавил {self.recipes} в избранное'


class ShoppingCart(BaseFavoritesandShoppingCart):

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзина'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipes'),
                name='Unique recipes in ShoppingCart'
            ),
        )

    def __str__(self):
        return f'Пользователь {self.user} добавил {self.recipes} в корзину'


class ShortLinkRecipe(models.Model):
    shortlink = models.CharField(
        verbose_name='Короткая ссылка',
        max_length=SHORT_LINK_DB,
        null=True,
        blank=True,
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        default=None,
    )
    full_link = models.URLField(unique=True)

    class Meta:
        verbose_name = 'Короткая ссылка'
        verbose_name_plural = 'Короткие ссылки'

    def save(self, *args, **kwargs):
        if not self.shortlink:
            while True:
                self.shortlink = ''.join(
                    choices(CHARACTERS, k=SHORT_LINK_DB)
                )
                if not ShortLinkRecipe.objects.filter(
                    shortlink=self.shortlink
                ).exists():
                    break
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.shortlink}'
