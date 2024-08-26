from django.urls import path, include
from rest_framework import routers

from api.views import (
    TagViewsets,
    IngredientsViewsets,
    UserViewsets,
    RecipeViewsets,
)


router = routers.DefaultRouter()
router.register(r'tags', TagViewsets)
router.register(r'ingredients', IngredientsViewsets)
router.register(r'users', UserViewsets)
router.register(r'recipes', RecipeViewsets)

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
