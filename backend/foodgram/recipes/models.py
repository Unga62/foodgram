from django.db import models
from django.contrib.auth import get_user_model
from random import choices

from recipes.validators import (
    validation_slug,
    validation_cooking_time,
    validation_amount_ingredients
)
from api.const import (
    TAGS_AND_SLUG_MAX_LENGTH,
    NAME_ING_MAX_LENGTH,
    MEASUREMENT_UNIT_MAX_LENGTH,
    RECIPES_NAME_MAX_LENGTH,
    SHORT_LINK_DB,
    CHARACTERS,
)

User = get_user_model()


class Tags (models.Model):
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


class Ingredients(models.Model):
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


class Recipes(models.Model):
    tags = models.ManyToManyField(
        Tags,
        verbose_name='Теги',
        related_name='recipes'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
    )
    ingredients = models.ManyToManyField(
        Ingredients,
        through='ArrayIngredients',
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


class ArrayIngredients(models.Model):
    recipes = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name='arrayingredients',
    )
    ingredients = models.ForeignKey(
        Ingredients,
        on_delete=models.CASCADE,
        related_name='arrayingredients',
    )
    amount = models.PositiveIntegerField(
        validators=(validation_amount_ingredients,),
        verbose_name='Количество ингредиентов',
    )

    class Meta:
        verbose_name = 'Количество ингредиентов'
        verbose_name_plural = 'Количество ингредиентов'

    def __str__(self):
        return (f'В рецепте {self.recipes} количество '
                f'ингридиетов {self.ingredients}-{self.amount}')


class BaseFavoritesandShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipes = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True


class Favorites(BaseFavoritesandShoppingCart):

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


class ShortLinkRecipes(models.Model):
    shortlink = models.CharField(
        verbose_name='Короткая ссылка',
        max_length=SHORT_LINK_DB,
        null=True,
        blank=True,
    )
    recipe = models.ForeignKey(
        Recipes,
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
                if not ShortLinkRecipes.objects.filter(
                    shortlink=self.shortlink
                ).exists():
                    break
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.shortlink}'
