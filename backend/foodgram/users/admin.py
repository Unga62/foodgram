from django.contrib import admin

from users.models import Users, Subscriptions

admin.site.register(Users)
admin.site.register(Subscriptions)
