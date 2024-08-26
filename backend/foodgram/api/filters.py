from django_filters.rest_framework import CharFilter, FilterSet

from recipes.models import Recipes


class RecipeFilter(FilterSet):

    tags = CharFilter(field_name='tags__slug', lookup_expr='iexact')
    author = CharFilter(field_name='author__id', lookup_expr='iexact')

    class Meta:
        model = Recipes
        fields = ('author', 'tags',)
