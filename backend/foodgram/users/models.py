from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError

from api.const import USERNAME_MAX_LENGTH, EMAIL_MAX_LENGTH


class Users(AbstractUser):
    email = models.EmailField(
        max_length=EMAIL_MAX_LENGTH,
        verbose_name='Электронная почта',
        unique=True
    )
    username = models.CharField(
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        verbose_name='Имя пользователя',
    )
    first_name = models.CharField(
        max_length=USERNAME_MAX_LENGTH,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=USERNAME_MAX_LENGTH,
        verbose_name='Фамилия',
    )
    avatar = models.ImageField(
        upload_to='users/avatar',
        verbose_name='Avatar',
        null=True,
        default=None,
        blank=True,
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self) -> str:
        return self.username


class Subscriptions(models.Model):

    user = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name='user',
        verbose_name='Пользователь'
    )
    following = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Подписчик'
    )

    def clean(self):
        if self.user == self.following:
            raise ValidationError(
                "Пользователь не может подписаться на самого себя."
            )

    def __str__(self):
        return f'Пользователь: {self.user}; Подписчик: {self.following}'

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'following'),
                name='Unique subscribers'
            ),
        )
