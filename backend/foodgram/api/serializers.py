import base64
from django.core.files.base import ContentFile
from rest_framework import serializers, status
from django.db.models import F
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from recipes.models import Tags, Ingredients, Recipes, ShoppingCart, Favorites, ArrayIngredients, ShortLinkRecipes
from users.models import Users
from api.const import USERNAME_MAX_LENGTH


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class TagSerializers(serializers.ModelSerializer):

    class Meta:
        model = Tags
        fields = ('id', 'name', 'slug')


class IngredientsSerializers(serializers.ModelSerializer):

    class Meta:
        model = Ingredients
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
    avatar = Base64ImageField()
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
        if user.is_anonymous or (user == obj):
            return False
        return user.following.filter(id=obj.id).exists()


class AvatarUserSerializer(serializers.ModelSerializer):

    avatar = Base64ImageField(allow_null=True)

    class Meta:
        model = Users
        fields = ('avatar',)


class ChangePasswordSerializer(serializers.ModelSerializer):
    new_password = serializers.CharField()
    current_password = serializers.CharField()

    class Meta:
        model = Users
        fields = ('new_password', 'current_password')


class FollowingSerializers(UserSerializer):

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
        model = Recipes
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
            amount=F('arrayingredients__amount'),
        )

    def get_is_favorited(self, obj):
        """Избранное."""
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Favorites.objects.filter(recipes=obj, user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        """Список покупок."""
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(recipes=obj, user=user).exists()


class CreateArrayIngredients(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredients.objects.all()
    )
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = ArrayIngredients
        fields = ('id', 'amount',)


class CreateRecipeSerializers(serializers.ModelSerializer):
    ingredients = CreateArrayIngredients(
        many=True,
        write_only=True,
        label='Ингредиенты',
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tags.objects.all(),
        label='Теги',
    )
    image = Base64ImageField(label='Изображение рецепта')

    class Meta:
        model = Recipes
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        )

    def validate_tags(self, data):
        if 'tags' not in data:
            raise ValidationError(
                'В рецепте должен быть минимум один тег.',
                Response(status=status.HTTP_400_BAD_REQUEST)
            )
        list_tags = []
        for i in data:
            if i in list_tags:
                raise ValidationError(
                    'Теги не должны повторяться.',
                    Response(status=status.HTTP_400_BAD_REQUEST)
                )
        return data

    def validate_ingredients(self, data):
        if 'ingredients' not in data:
            raise ValidationError(
                'В рецепте должен быть минимум один ингредиент.',
                Response(status=status.HTTP_400_BAD_REQUEST)
            )
        list_ingredients = []
        for i in data:
            if i in list_ingredients:
                raise ValidationError(
                    'Ингредиент не должны повторяться.',
                    Response(status=status.HTTP_400_BAD_REQUEST)
                )
        return data

    def create_ingredients(self, ingredients, recipes):
        for ingredient in ingredients:
            ArrayIngredients.objects.create(
                recipes=recipes,
                ingredients=ingredient['id'],
                amount=ingredient['amount']
            )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipes = Recipes.objects.create(**validated_data)
        self.create_ingredients(ingredients, recipes)
        recipes.tags.set(tags)
        return recipes


class ShortLinkSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShortLinkRecipes
        fields = ('shortlink', 'recipe', 'full_link',)
        read_only = ('shortlink',)
