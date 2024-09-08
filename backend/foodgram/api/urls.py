from django.urls import include, path
from rest_framework import routers

from api.views import (
    IngredientsViewset,
    RecipeViewset,
    TagViewset,
    UserViewset,
)

router = routers.DefaultRouter()
router.register(r'tags', TagViewset)
router.register(r'ingredients', IngredientsViewset)
router.register(r'users', UserViewset)
router.register(r'recipes', RecipeViewset)

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
