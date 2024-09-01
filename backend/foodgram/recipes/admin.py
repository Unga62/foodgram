from django.contrib import admin
from recipes.models import (
    ArrayIngredients,
    Favorites,
    Ingredients,
    Recipes,
    ShoppingCart,
    ShortLinkRecipes,
    Tags,
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


admin.site.register(Tags)
admin.site.register(Ingredients, IngredientsAdmin)
admin.site.register(Recipes, RecipesAdmin)
admin.site.register(ArrayIngredients)
admin.site.register(Favorites)
admin.site.register(ShoppingCart)
admin.site.register(ShortLinkRecipes)
