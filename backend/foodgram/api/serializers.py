import random
import string

from django.db.models import F
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from api.const import USERNAME_MAX_LENGTH
from api.fields import Base64ImageField
from recipes.models import (
    ArrayIngredient,
    Favorite,
    Ingredient,
    Recipe,
    ShoppingCart,
    ShortLinkRecipe,
    Tag,
)
from users.models import Subscription, User


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class CreateUsersSerializer(UserCreateSerializer):
    username = serializers.RegexField(
        regex=r'^[\w.@+-]+\Z',
        max_length=USERNAME_MAX_LENGTH,
        label='Ник')

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'password',
        )


class UsersSerializer(UserSerializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    is_subscribed = serializers.SerializerMethodField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    username = serializers.CharField()
    avatar = Base64ImageField(required=False)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=user,
            following=obj.id
        ).exists()


class AvatarUserSerializer(serializers.ModelSerializer):

    avatar = Base64ImageField(allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)


class ChangePasswordSerializer(serializers.ModelSerializer):
    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ('current_password', 'new_password')

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                'Ваш старый пароль был введен неверно.',
                Response(status=status.HTTP_400_BAD_REQUEST)
            )
        return value


class ReadRecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(read_only=True, many=True)
    author = UsersSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
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
        """Cписок ингредиентов для рецепта."""
        return obj.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('array_ingredients__amount'),
        )

    def base_favorited_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return obj.filter(
            user=user
        ).exists()

    def get_is_favorited(self, obj):
        """Избранное."""
        return self.base_favorited_shopping_cart(obj.favorites)

    def get_is_in_shopping_cart(self, obj):
        """Список покупок."""
        return self.base_favorited_shopping_cart(obj.shopping_list)


class CreateArrayIngredients(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = ArrayIngredient
        fields = ('id', 'amount',)


class UpdateCreateRecipeSerializers(serializers.ModelSerializer):
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
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance = super().update(instance, validated_data)
        instance.tags.clear()
        instance.ingredients.clear()
        instance.tags.set(tags)
        self.create_ingredients(ingredients=ingredients, recipes=instance)
        return instance

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return ReadRecipeSerializer(instance, context=context).data


class ShortLinkSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShortLinkRecipe
        fields = ('shortlink', 'recipe', 'full_link',)
        read_only = ('shortlink',)
        write_only_fields = ('full_link', 'recipe')

    def shortlink(self):
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(6))

    def create(self, validated_data):
        try:
            return ShortLinkRecipe.objects.get(
                recipe=validated_data['recipe'].id,
                full_link=validated_data['full_link'])
        except Exception:
            return ShortLinkRecipe.objects.create(
                recipe=validated_data['recipe'],
                full_link=validated_data['full_link'],
                shortlink=self.shortlink()
            )


class ForFavoritesandShoppingCartSerializer(ReadRecipeSerializer):

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
        except self.Meta.model.DoesNotExist:
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
        return self.Meta.model.objects.create(
            user=user,
            recipes=recipes
        )


class FavoritesSerializer(FavoritesandShoppingCartSerializer):

    class Meta:
        model = Favorite
        fields = ('recipes',)


class ShoppingCartSerializer(FavoritesandShoppingCartSerializer):

    class Meta:
        model = ShoppingCart
        fields = ('recipes',)


class SubscriptionsUserSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='following.id')
    email = serializers.ReadOnlyField(source='following.email')
    username = serializers.ReadOnlyField(source='following.username')
    first_name = serializers.ReadOnlyField(source='following.first_name')
    last_name = serializers.ReadOnlyField(source='following.last_name')
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
            'recipes',
            'recipes_count'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=user,
            following=obj.following
        ).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        queryset = Recipe.objects.filter(author=obj.following)
        if limit:
            queryset = queryset[:int(limit)]
        return ForFavoritesandShoppingCartSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.following).count()
