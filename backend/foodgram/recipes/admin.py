from django.contrib import admin

from recipes.models import (
    ArrayIngredient,
    Favorite,
    Ingredient,
    Recipe,
    ShoppingCart,
    ShortLinkRecipe,
    Tag,
)


class RecipesAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
    )
    search_fields = ('name', 'author')
    list_filter = ('tags',)


class IngredientsAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit',
    )
    search_fields = ('name',)


admin.site.register(Tag)
admin.site.register(Ingredient, IngredientsAdmin)
admin.site.register(Recipe, RecipesAdmin)
admin.site.register(ArrayIngredient)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
admin.site.register(ShortLinkRecipe)
