from django.db.models import F
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.validators import UniqueTogetherValidator
from django.core.exceptions import ObjectDoesNotExist

from api.const import USERNAME_MAX_LENGTH
from recipes.models import (
    ArrayIngredient,
    Favorite,
    Ingredient,
    Recipe,
    ShoppingCart,
    ShortLinkRecipe,
    Tag,
)
from users.models import Subscriptions, Users
from api.fields import Base64ImageField


class TagSerializers(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientsSerializers(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class CreateUsersSerializers(UserCreateSerializer):
    username = serializers.RegexField(
        regex=r'^[\w.@+-]+\Z',
        max_length=USERNAME_MAX_LENGTH,
        label='Ник')

    class Meta:
        model = Users
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'password',
        )


class UsersSerializers(UserSerializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    is_subscribed = serializers.SerializerMethodField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    username = serializers.CharField()
    avatar = Base64ImageField(required=False)

    class Meta:
        model = Users
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous or user == obj:
            return False
        return user.following.filter(id=obj.id).exists()

    def update(self, instance, validated_data):
        user = self.context.get('request').user
        if user != instance.id:
            raise ValidationError(
                'Вы не можете редактировать чужой профиль',
                Response(status=status.HTTP_403_FORBIDDEN)
            )
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.first_name = validated_data.get(
            'first_name', instance.first_name
        )
        instance.last_name = validated_data.get(
            'last_name', instance.last_name
        )
        instance.save()
        return instance


class AvatarUserSerializer(serializers.ModelSerializer):

    avatar = Base64ImageField(allow_null=True)

    class Meta:
        model = Users
        fields = ('avatar',)


class ChangePasswordSerializer(serializers.ModelSerializer):
    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)

    class Meta:
        model = Users
        fields = ('current_password', 'new_password')

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                'Ваш старый пароль был введен неверно.',
                Response(status=status.HTTP_400_BAD_REQUEST)
            )
        return value


class ReadRecipeSerializers(serializers.ModelSerializer):
    tags = TagSerializers(read_only=True, many=True)
    author = UsersSerializers(read_only=True)
    ingredients = serializers.SerializerMethodField(read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    name = serializers.CharField(read_only=True)
    image = Base64ImageField(read_only=True)
    text = serializers.CharField(read_only=True)
    cooking_time = serializers.IntegerField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_ingredients(self, obj):
        """Cписок ингридиентов для рецепта."""
        return obj.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('array_ingredients__amount'),
        )

    def base_favorited_shopping_cart(self):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False

    def get_is_favorited(self, obj):
        """Избранное."""
        return Favorite.objects.filter(
            recipes=obj, user=self.base_favorited_shopping_cart()
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        """Список покупок."""
        return ShoppingCart.objects.filter(
            recipes=obj, user=self.base_favorited_shopping_cart()
        ).exists()


class CreateArrayIngredients(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = ArrayIngredient
        fields = ('id', 'amount',)


class CreateRecipeSerializers(serializers.ModelSerializer):
    ingredients = CreateArrayIngredients(
        many=True,
        write_only=True,
        label='Ингредиенты',
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        label='Теги',
    )
    image = Base64ImageField(label='Изображение рецепта')

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        )

    def validate_tags(self, data):
        tags = []
        for tag in data:
            if tag in tags:
                raise ValidationError(
                    'Теги не должны повторяться.',
                    Response(status=status.HTTP_400_BAD_REQUEST)
                )
            tags.append(tag)
        return data

    def validate_ingredients(self, data):
        ingredients = []
        for ingredient in data:
            if ingredient in ingredients:
                raise ValidationError(
                    'Ингредиент не должны повторяться.',
                    Response(status=status.HTTP_400_BAD_REQUEST)
                )
            ingredients.append(ingredient)
        return data

    def create_ingredients(self, ingredients, recipes):
        ingredient_recipes = []
        for ingredient in ingredients:
            ingredient_recipes.append(
                ArrayIngredient(
                    recipes=recipes,
                    ingredients=ingredient['id'],
                    amount=ingredient['amount']
                )
            )
        ArrayIngredient.objects.bulk_create(ingredient_recipes)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipes = Recipe.objects.create(**validated_data)
        self.create_ingredients(ingredients, recipes)
        recipes.tags.set(tags)
        return recipes

    def update(self, instance, validated_data):
        user = self.context.get('request').user
        if user != instance.author:
            raise ValidationError(
                'Вы не можете редактировать чужой рецепт',
                Response(status=status.HTTP_403_FORBIDDEN)
            )
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance = super().update(instance, validated_data)
        instance.tags.set(tags)
        self.create_ingredients(ingredients, instance)
        instance.save()
        return instance

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return ReadRecipeSerializers(instance, context=context).data


class ShortLinkSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShortLinkRecipe
        fields = ('shortlink', 'recipe', 'full_link',)
        read_only = ('shortlink',)


class ForFavoritesandShoppingCartSerializer(ReadRecipeSerializers):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)


class FavoritesandShoppingCartSerializer(serializers.ModelSerializer):
    recipes = ForFavoritesandShoppingCartSerializer(read_only=True)

    def to_internal_value(self, data):
        user = data.get('user')
        recipes = data.get('recipes')
        try:
            self.Meta.model.objects.get(
                recipes=recipes,
                user=user
            )
        except ObjectDoesNotExist:
            return {
                'user': user,
                'recipes': recipes
            }
        if recipes:
            raise ValidationError(
                {
                    'Ошибка': 'Данный рецепт уже в списке'
                }
            )

    def create(self, validated_data):
        user = validated_data.get('user')
        recipes = validated_data.get('recipes')
        obj = self.Meta.model.objects.create(
            user=user,
            recipes=recipes
        )
        return obj


class FavoritesSerializer(FavoritesandShoppingCartSerializer): 

    class Meta:
        model = Favorite
        fields = ('recipes',)


class ShoppingCartSerializer(FavoritesandShoppingCartSerializer):

    class Meta:
        model = ShoppingCart
        fields = ('recipes',)


class CreateSubscriptionsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscriptions
        fields = ('user', 'following')
        validators = [
            UniqueTogetherValidator(
                queryset=Subscriptions.objects.all(),
                fields=['user', 'following']
            )
        ]

    def validate(self, data):
        if data['user'] == data['following']:
            raise ValidationError(
                'Нельзя подписаться на самого себя',
                Response(status=status.HTTP_400_BAD_REQUEST)
            )
        return data

    def create(self, validated_data):
        return Subscriptions.objects.create(
            user=validated_data['user'],
            following=validated_data['following'],
        )


class SubscriptionsUserSerializer(serializers.ModelSerializer):
    recipes_set = ForFavoritesandShoppingCartSerializer(
        read_only=True,
        many=True,
    )
    recipes_count = serializers.SerializerMethodField(read_only=True)
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Users
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
            'avatar',
            'recipes_count',
            'recipes_set',
        )

    def get_recipes_count(self, obj):
        return Recipe.objects.count()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        subscribed = {
            'user': obj.id,
            'following': request.user.id
        }
        serializer = CreateSubscriptionsSerializer(data=subscribed)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return True


class ReadSubscriptionsUserSerializer(SubscriptionsUserSerializer):
    def get_is_subscribed(self, obj):
        return True
