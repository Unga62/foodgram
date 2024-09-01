from api.views import (
    IngredientsViewsets,
    RecipeViewsets,
    TagViewsets,
    UserViewsets,
)
from django.urls import include, path
from rest_framework import routers

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
