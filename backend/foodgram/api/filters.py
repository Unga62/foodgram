from django_filters import CharFilter, FilterSet
from recipes.models import Favorites, Recipes, ShoppingCart


def get_filter_queryset(self):
    queryset = Recipes.objects.all()
    user = self.request.user
    is_favorited = self.request.GET.get('is_favorited')
    is_in_shopping_cart = self.request.GET.get('is_in_shopping_cart')
    if is_favorited and user.is_authenticated:
        obj = Favorites.objects.filter(user=user)
        recipes_id = obj.values_list('recipes_id', flat=True)
        queryset = queryset.filter(id__in=recipes_id)
    if is_in_shopping_cart and user.is_authenticated:
        obj = ShoppingCart.objects.filter(user=user)
        recipes_id = obj.values_list('recipes_id', flat=True)
        queryset = queryset.filter(id__in=recipes_id)
    return queryset


class RecipesFilter(FilterSet):
    tags = CharFilter(
        field_name='tags__slug',
        lookup_expr='iexact'
    )

    class Meta:
        model = Recipes
        fields = ('tags', 'author')
