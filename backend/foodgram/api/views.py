from rest_framework import viewsets, status, filters
from django.contrib.sites.shortcuts import get_current_site
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404, redirect

from api.filters import RecipeFilter
from recipes.models import Tags, Ingredients, Recipes, ShortLinkRecipes
from users.models import Users
from api.serializers import (
    TagSerializers,
    IngredientsSerializers,
    UsersSerializers,
    CreateUsersSerializers,
    FollowingSerializers,
    AvatarUserSerializer,
    ChangePasswordSerializer,
    ReadRecipeSerializers,
    CreateRecipeSerializers,
    ShortLinkSerializer,
)
from api.pagination import CustomPagination


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
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateRecipeSerializers
        return ReadRecipeSerializers

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def perform_update(self, serializer):
        return serializer.save(author=self.request.user)

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


def redirection(request, shortlink):
    return redirect(
        get_object_or_404(
            ShortLinkRecipes.objects, shortlink=shortlink
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
    def subscriptions(self, request):
        """Просмотор подписчиков пользователя."""
        user = self.request.user
        authors = user.is_subscribed.all()
        serializer = FollowingSerializers(
            authors, many=True, context={'request': request}
        )
        return Response(serializer.data)

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

