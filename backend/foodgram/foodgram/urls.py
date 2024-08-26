from django.contrib import admin
from django.urls import path, include

from api.views import redirection


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('<shortlink>/', redirection, name='redirection'),
]
