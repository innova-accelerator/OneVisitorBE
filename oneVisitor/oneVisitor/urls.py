from django.urls import path, include

urlpatterns = [
    path('api/auth/', include('accounts.urls')),
    path('api/', include('analytics.urls')),
    path('api/sites/', include('sites.urls')),
]