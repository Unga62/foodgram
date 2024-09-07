from django.contrib import admin
from users.models import Subscription, User

admin.site.register(User)
admin.site.register(Subscription)
