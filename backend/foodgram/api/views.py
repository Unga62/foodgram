from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.filters import RecipesFilter, IngredientFilter
from api.mixins import PaginationMixins
from api.pagination import CustomPagination
from api.permissions import CreateUpadateDeletePermissions
from api.serializers import (
    AvatarUserSerializer,
    ChangePasswordSerializer,
    UpdateCreateRecipeSerializers,
    CreateUsersSerializer,
    FavoritesSerializer,
    IngredientsSerializer,
    ReadRecipeSerializer,
    ShoppingCartSerializer,
    ShortLinkSerializer,
    SubscriptionsUserSerializer,
    TagSerializer,
    UsersSerializer,
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    ShoppingCart,
    ShortLinkRecipe,
    Tag,
)
from users.models import Subscription, User


class TagViewset(viewsets.ReadOnlyModelViewSet):
    """Вьюсет тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class IngredientsViewset(viewsets.ReadOnlyModelViewSet):
    """Вьюсет ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    permission_classes = (AllowAny,)
    filter_backends = (IngredientFilter, )
    search_fields = ('^name',)


class RecipeViewset(viewsets.ModelViewSet, PaginationMixins):
    queryset = Recipe.objects.all()
    serializer_class = ReadRecipeSerializer
    permission_classes = (AllowAny, CreateUpadateDeletePermissions,)
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipesFilter

    def get_serializer_class(self):
        if self.request.method == 'POST' or self.request.method == 'PATCH':
            return UpdateCreateRecipeSerializers
        return ReadRecipeSerializer

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    @action(
        detail=True,
        url_path='get-link',
        methods=['GET']
    )
    def shortlink(self, request, pk):
        host = get_current_site(request)
        data = {'recipe': pk,
                'full_link': f'http://{host}/recipes/{pk}'}
        serializer = ShortLinkSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        shortlink = serializer.data.get('shortlink')
        return Response({'short-link': f'http://{host}/s/{shortlink}/'})

    def add_or_delete_favorite_shopping_cart(
            self,
            request,
            serializers,
            model,
            pk
    ):
        recipes = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            recipes_user = {
                'recipes': recipes,
                'user': request.user
            }
            serializer = serializers(
                data=recipes_user,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                serializer.data.get('recipes'),
                status=status.HTTP_201_CREATED
            )
        get_object_or_404(model, user=request.user, recipes=recipes).delete()
        return Response(
            'Рецепт удален из списка.',
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=(IsAuthenticated,),
        url_path='favorite',
    )
    def favorite(self, request, pk):
        return self.add_or_delete_favorite_shopping_cart(
            request,
            FavoritesSerializer,
            Favorite,
            pk
        )

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=(IsAuthenticated,),
        url_path='shopping_cart',
    )
    def is_in_shopping_cart(self, request, pk):
        return self.add_or_delete_favorite_shopping_cart(
            request,
            ShoppingCartSerializer,
            ShoppingCart,
            pk
        )

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart'
    )
    def download_shopping_cart(self, request):
        author = request.user
        shopping_cart = ShoppingCart.objects.filter(user=author)
        ingredients = {}
        for ing in shopping_cart:
            recipe_ingredients = ing.recipes.array_ingredients.all()
            for ingredient in recipe_ingredients:
                name = ingredient.ingredients.name
                unit = ingredient.ingredients.measurement_unit
                amount = ingredient.amount
                if name in ingredients:
                    ingredients[name]['amount'] += amount
                else:
                    ingredients[name] = {
                        'amount': amount,
                        'unit': unit,
                    }
        shopping_cart_ingredients = ''
        for ingredient, data in ingredients.items():
            shopping_cart_ingredients += (f"{ingredient}: ({data['unit']}) — "
                                          f"{data['amount']}\n")
        response = HttpResponse(
            shopping_cart_ingredients,
            content_type='text/plain'
        )
        response['Content-Disposition'] = (
            'attachment;'
            'filename="shopping_list.txt"'
        )
        return response


def redirection(request, shortlink):
    return redirect(
        get_object_or_404(
            ShortLinkRecipe,
            shortlink=shortlink
        ).full_link
    )


class UserViewset(viewsets.ModelViewSet, PaginationMixins):
    """Вьюсет пользователя."""
    queryset = User.objects.all()
    serializer_class = UsersSerializer
    permission_classes = (AllowAny,)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateUsersSerializer
        return UsersSerializer

    @action(detail=False, url_path='me', permission_classes=(IsAuthenticated,))
    def user_me(self, request):
        """Просмотр профиля пользователя."""
        user = self.request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        url_path='me/avatar',
        methods=['PUT', 'DELETE'],
        permission_classes=(IsAuthenticated,)
    )
    def change_avatar(self, request):
        """Изменение аватара."""
        if self.request.method == 'PUT':
            serializer = AvatarUserSerializer(
                request.user, data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = AvatarUserSerializer(
            request.user,
            data={'avatar': None}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        url_path='set_password',
        methods=['POST'],
        permission_classes=(IsAuthenticated,)
    )
    def change_password(self, request):
        """Изменение пароля."""
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.data.get('new_password'))
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        user = request.user
        queryset = Subscription.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionsUserSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, pk=None):
        user = request.user
        subscribed = get_object_or_404(User, id=pk)
        followings = Subscription.objects.filter(
            user=user,
            following=subscribed
        )
        if request.method != 'POST':
            try:
                followings.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Exception:
                return Response(
                    'Вы не подписаны на данного пользователя',
                    status=status.HTTP_400_BAD_REQUEST
                )
        create_followings = Subscription.objects.create(
            user=user,
            following=subscribed
        )
        serializer = SubscriptionsUserSerializer(
            create_followings,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
