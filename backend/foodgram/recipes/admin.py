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

admin.site.register(Tags)
admin.site.register(Ingredients)
admin.site.register(Recipes)
admin.site.register(ArrayIngredients)
admin.site.register(Favorites)
admin.site.register(ShoppingCart)
admin.site.register(ShortLinkRecipes)
