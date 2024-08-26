from django.contrib import admin

from recipes.models import (
    Tags,
    Ingredients,
    Recipes,
    ArrayIngredients,
    Favorites,
    ShoppingCart,
    ShortLinkRecipes
)

admin.site.register(Tags)
admin.site.register(Ingredients)
admin.site.register(Recipes)
admin.site.register(ArrayIngredients)
admin.site.register(Favorites)
admin.site.register(ShoppingCart)
admin.site.register(ShortLinkRecipes)
