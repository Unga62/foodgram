from api.filters import RecipesFilter, get_filter_queryset
from api.pagination import CustomPagination
from api.serializers import (
    AvatarUserSerializer,
    ChangePasswordSerializer,
    CreateRecipeSerializers,
    CreateUsersSerializers,
    DownloadShoppingCartSerializer,
    FavoritesSerializer,
    IngredientsSerializers,
    ReadRecipeSerializers,
    ReadSubscriptionsUserSerializer,
    ShoppingCartSerializer,
    ShortLinkSerializer,
    SubscriptionsUserSerializer,
    TagSerializers,
    UsersSerializers,
)
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import (
    Favorites,
    Ingredients,
    Recipes,
    ShoppingCart,
    ShortLinkRecipes,
    Tags,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from users.models import Subscriptions, Users


class PaginationMixins(viewsets.GenericViewSet):
    pagination_class = CustomPagination


class TagViewsets(viewsets.ReadOnlyModelViewSet):
    """Вьюсет тегов."""
    queryset = Tags.objects.all()
    serializer_class = TagSerializers
    permission_classes = (AllowAny,)


class IngredientsViewsets(viewsets.ReadOnlyModelViewSet):
    """Вьюсет ингредиентов."""
    queryset = Ingredients.objects.all()
    serializer_class = IngredientsSerializers
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    search_fields = ('^name',)


class RecipeViewsets(viewsets.ModelViewSet, PaginationMixins):
    queryset = Recipes.objects.all()
    serializer_class = ReadRecipeSerializers
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipesFilter

    def get_queryset(self):
        return get_filter_queryset(self)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateRecipeSerializers
        return ReadRecipeSerializers

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def perform_update(self, serializer):
        instance = self.get_object()
        if self.request.user != instance.author:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return serializer.save()

    def destroy(self, request, pk):
        instance = self.get_object()
        if request.user != instance.author:
            return Response(
                'Вы не можете удалить чужой рецепт.',
                status=status.HTTP_401_UNAUTHORIZED)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, url_path='get-link', methods=['GET'])
    def get_shortlink(self, request, pk):
        host = get_current_site(request)
        data = {'recipe': pk,
                'full_link': f'http://{host}/api/recipes/{pk}'}
        serializer = ShortLinkSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        shortlink = serializer.data.get('shortlink')
        return Response(
            {'shortlink': f'http://{host}/{shortlink}'},
            status=status.HTTP_200_OK
        )

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=(IsAuthenticated,),
        url_path='favorite',
    )
    def is_favorited(self, request, *args, **kwargs):
        recipes = get_object_or_404(Recipes, id=self.kwargs.get('pk'))
        user = self.request.user
        if request.method == 'POST':
            if Favorites.objects.filter(
                user=user,
                recipes=recipes
            ).exists():
                return Response(
                    'Рецепт уже добавлен!',
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = FavoritesSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save(user=user, recipe=recipes)
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        Favorites.objects.get(recipes=recipes).delete()
        return Response(
            'Рецепт удалён из избранного.',
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=(IsAuthenticated,),
        url_path='shopping_cart',
    )
    def is_in_shopping_cart(self, request, *args, **kwargs):
        recipes = get_object_or_404(Recipes, id=self.kwargs.get('pk'))
        user = self.request.user
        if request.method == 'POST':
            if ShoppingCart.objects.filter(
                user=user,
                recipes=recipes
            ).exists():
                return Response(
                    'Рецепт уже добавлен!',
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = ShoppingCartSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save(user=user, recipe=recipes)
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        ShoppingCart.objects.get(recipes=recipes).delete()
        return Response(
            'Рецепт удалён из списка покупок.',
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart'
    )
    def download_shopping_cart(self, request):
        serializer = DownloadShoppingCartSerializer(
            context={'request': request})
        response = serializer.download_csv()
        return response


def redirection(request, shortlink):
    return redirect(
        get_object_or_404(
            ShortLinkRecipes.objects,
            shortlink=shortlink
        ).full_link
    )


class UserViewsets(viewsets.ModelViewSet, PaginationMixins):
    """Вьюсет пользователя."""
    queryset = Users.objects.all()
    permission_classes = (AllowAny,)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateUsersSerializers
        return UsersSerializers

    @action(detail=False, url_path='me', permission_classes=(IsAuthenticated,))
    def user_me(self, request):
        """Просмотр профиля пользователя."""
        user = self.request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def update_user(self, instance, validated_data):
        """Изменение данных пользователя."""
        instance.name = validated_data.get('name', instance.name)
        instance.email = validated_data.get('email', instance.email)
        instance.first_name = validated_data.get(
            'first_name', instance.first_name
        )
        instance.last_name = validated_data.get(
            'last_name', instance.last_name
        )
        instance.save()
        return instance

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
        if self.request.method == 'DELETE':
            serializer = AvatarUserSerializer(
                request.user, data={'avatar': None})
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
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if user.check_password(serializer.data.get('current_password')):
                user.set_password(serializer.data.get('new_password'))
                user.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=(IsAuthenticated,),
        url_path='subscribe',
    )
    def subscriptions(self, request, pk=None):
        user = get_object_or_404(Users, id=pk)
        if self.request.method == 'POST':
            serializer = SubscriptionsUserSerializer(
                user,
                context={'request': request}
            )
            if not serializer.data.get('errors'):
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                serializer.data,
                status=status.HTTP_400_BAD_REQUEST
            )
        elif self.request.method == 'DELETE':
            try:
                delete_subscriptions = get_object_or_404(
                    Subscriptions,
                    following=request.user.id,
                    user=user.id
                )
            except Exception:
                return Response(
                    'Вы не подписаны на данного пользователя',
                    status=status.HTTP_400_BAD_REQUEST
                )
        delete_subscriptions.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=(IsAuthenticated,),
        url_path='subscriptions'
    )
    def subscriptions_get(self, request):
        user = request.user
        subscriptions = user.following.all().values_list(
            'following',
            flat=True
        )
        subscriptions_users = Users.objects.filter(id__in=subscriptions)
        page = self.paginate_queryset(subscriptions_users)
        if page is not None:
            serializer = ReadSubscriptionsUserSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ReadSubscriptionsUserSerializer(
            subscriptions_users,
            many=True
        )
        return Response(serializer.data)
