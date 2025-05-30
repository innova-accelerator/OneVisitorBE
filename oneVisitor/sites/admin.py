from django.contrib import admin
from .models import Site, Host, Visitor, visitorPhoto

@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ['name', 'tenantId', 'published', 'lastPublished', 'url']
    list_filter = ['published', 'language']
    search_fields = ['name', 'tenantId', 'url']
    readonly_fields = ['lastPublished']  # Since this is auto-managed

@admin.register(Host)
class HostAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'department', 'site']
    list_filter = ['department', 'site']
    search_fields = ['name', 'email', 'department']

@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'company', 'host', 'site', 'visitorType']
    list_filter = ['visitorType', 'site', 'host']
    search_fields = ['name', 'email', 'company']

@admin.register(visitorPhoto)
class VisitorPhotoAdmin(admin.ModelAdmin):
    list_display = ['visitor', 'file']
    list_filter = ['visitor__site']