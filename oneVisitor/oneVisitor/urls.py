from django.urls import path, include

urlpatterns = [
    path('api/auth/', include('user.urls')),
    path('api/sites/', include('sites.urls')),
]