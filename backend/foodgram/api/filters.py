from django_filters import CharFilter, FilterSet, filters

from recipes.models import Recipe


class RecipesFilter(FilterSet):
    tags = CharFilter(
        field_name='tags__slug',
        lookup_expr='iexact'
    )

    is_favorited = filters.BooleanFilter(
        method='get_is_favorited',
        label='Избранное',
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='get_is_in_shopping_cart',
        label='Корзина',
    )

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_cart'
        )

    def get_is_favorited(self, queryset, name, value):
        return Recipe.objects.filter(favorites__user=self.request.user)

    def get_is_in_shopping_cart(self, queryset, name, value):
        return Recipe.objects.filter(shoppingcart__user=self.request.user)
