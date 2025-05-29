from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Site, SiteMember, SiteDomain, SiteSettings
from .serializers import (
    SiteSerializer, SiteMemberSerializer,
    SiteDomainSerializer, SiteSettingsSerializer
)
from .permissions import IsSiteOwnerOrAdmin

class SiteViewSet(viewsets.ModelViewSet):
    serializer_class = SiteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Site.objects.filter(
            members__user=self.request.user,
            members__is_active=True
        )

    def perform_create(self, serializer):
        site = serializer.save(owner=self.request.user)
        # Create default settings
        SiteSettings.objects.create(site=site)
        # Add owner as member
        SiteMember.objects.create(
            site=site,
            user=self.request.user,
            role='owner'
        )

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        site = self.get_object()
        if not IsSiteOwnerOrAdmin().has_object_permission(request, self, site):
            return Response(
                {"detail": "Only owners and admins can add members."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = SiteMemberSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(site=site)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def verify_domain(self, request, pk=None):
        site = self.get_object()
        domain = request.data.get('domain')
        verification_code = request.data.get('verification_code')

        try:
            site_domain = site.domains.get(domain=domain)
            if site_domain.verification_code == verification_code:
                site_domain.verified = True
                site_domain.save()
                return Response({"status": "verified"})
            return Response(
                {"detail": "Invalid verification code"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except SiteDomain.DoesNotExist:
            return Response(
                {"detail": "Domain not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class SiteSettingsViewSet(viewsets.ModelViewSet):
    serializer_class = SiteSettingsSerializer
    permission_classes = [permissions.IsAuthenticated, IsSiteOwnerOrAdmin]

    def get_queryset(self):
        return SiteSettings.objects.filter(
            site__members__user=self.request.user,
            site__members__is_active=True
        )