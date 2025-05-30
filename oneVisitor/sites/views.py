from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Site, Visitor, visitorPhoto
from .serializers import (
    SiteListSerializer, SiteDetailSerializer, SiteCreateUpdateSerializer,
    VisitorListSerializer, VisitorDetailSerializer, VisitorCreateSerializer,
    VisitorPhotoSerializer, SiteWithVisitorsSerializer
)


class SiteViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Site model
    """
    queryset = Site.objects.all()
    # permission_classes = [IsAuthenticated]  # Uncomment if authentication required
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return SiteListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return SiteCreateUpdateSerializer
        else:
            return SiteDetailSerializer
    
    def get_queryset(self):
        """Filter sites based on query parameters"""
        queryset = Site.objects.all()
        
        # Filter by published status
        published = self.request.query_params.get('published', None)
        if published is not None:
            queryset = queryset.filter(published=published.lower() == 'true')
        
        # Filter by tenant ID
        tenant_id = self.request.query_params.get('tenantId', None)
        if tenant_id is not None:
            queryset = queryset.filter(tenantId=tenant_id)
        
        # Search by name
        search = self.request.query_params.get('search', None)
        if search is not None:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset.order_by('-id')
    
    def create(self, request, *args, **kwargs):
        """Create a new site"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        site = serializer.save()
        
        # Return detailed response
        response_serializer = SiteDetailSerializer(site)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Update site (PUT)"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        site = serializer.save()
        
        # Return detailed response
        response_serializer = SiteDetailSerializer(site)
        return Response(response_serializer.data)
    
    @action(detail=True, methods=['get'])
    def visitors(self, request, pk=None):
        """Get all visitors for a specific site"""
        site = self.get_object()
        visitors = site.visitor.all().order_by('-id')
        
        # Pagination
        page = self.paginate_queryset(visitors)
        if page is not None:
            serializer = VisitorListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = VisitorListSerializer(visitors, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publish/unpublish a site"""
        site = self.get_object()
        site.published = not site.published
        site.save()
        
        serializer = SiteDetailSerializer(site)
        return Response({
            'message': f'Site {"published" if site.published else "unpublished"} successfully',
            'data': serializer.data
        })


class VisitorViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Visitor model
    """
    queryset = Visitor.objects.all()
    # permission_classes = [IsAuthenticated]  # Uncomment if authentication required
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return VisitorListSerializer
        elif self.action == 'create':
            return VisitorCreateSerializer
        else:
            return VisitorDetailSerializer
    
    def get_queryset(self):
        """Filter visitors based on query parameters"""
        queryset = Visitor.objects.select_related('site').prefetch_related('visitorPhoto')
        
        # Filter by site
        site_id = self.request.query_params.get('site', None)
        if site_id is not None:
            queryset = queryset.filter(site_id=site_id)
        
        # Filter by visitor type
        visitor_type = self.request.query_params.get('visitorType', None)
        if visitor_type is not None:
            queryset = queryset.filter(visitorType=visitor_type)
        
        # Filter by host
        host = self.request.query_params.get('host', None)
        if host is not None:
            queryset = queryset.filter(host__icontains=host)
        
        # Search by name or email
        search = self.request.query_params.get('search', None)
        if search is not None:
            queryset = queryset.filter(
                models.Q(name__icontains=search) | 
                models.Q(email__icontains=search) |
                models.Q(company__icontains=search)
            )
        
        return queryset.order_by('-id')
    
    def create(self, request, *args, **kwargs):
        """Create a new visitor"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            visitor = serializer.save()
        
        # Return detailed response
        response_serializer = VisitorDetailSerializer(visitor)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Update visitor (PUT/PATCH)"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Use create serializer for updates
        serializer = VisitorCreateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        visitor = serializer.save()
        
        # Return detailed response
        response_serializer = VisitorDetailSerializer(visitor)
        return Response(response_serializer.data)
    
    @action(detail=True, methods=['get'])
    def photos(self, request, pk=None):
        """Get all photos for a specific visitor"""
        visitor = self.get_object()
        photos = visitor.visitorPhoto.all()
        serializer = VisitorPhotoSerializer(photos, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_photo(self, request, pk=None):
        """Upload a photo for a visitor"""
        visitor = self.get_object()
        
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        photo_data = {
            'file': request.FILES['file'],
            'visitor': visitor.id
        }
        
        serializer = VisitorPhotoSerializer(data=photo_data)
        serializer.is_valid(raise_exception=True)
        photo = serializer.save(visitor=visitor)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class VisitorPhotoViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for VisitorPhoto model
    """
    queryset = visitorPhoto.objects.all()
    serializer_class = VisitorPhotoSerializer
    parser_classes = [MultiPartParser, FormParser]
    # permission_classes = [IsAuthenticated]  # Uncomment if authentication required
    
    def get_queryset(self):
        """Filter photos based on visitor"""
        queryset = visitorPhoto.objects.select_related('visitor')
        
        # Filter by visitor
        visitor_id = self.request.query_params.get('visitor', None)
        if visitor_id is not None:
            queryset = queryset.filter(visitor_id=visitor_id)
        
        return queryset.order_by('-id')
    
    def create(self, request, *args, **kwargs):
        """Upload a new visitor photo"""
        if 'visitor' not in request.data:
            return Response(
                {'error': 'Visitor ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify visitor exists
        visitor_id = request.data['visitor']
        visitor = get_object_or_404(Visitor, id=visitor_id)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        photo = serializer.save(visitor=visitor)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def destroy(self, request, *args, **kwargs):
        """Delete a visitor photo"""
        photo = self.get_object()
        
        # Delete the file from storage
        if photo.file:
            photo.file.delete(save=False)
        
        photo.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Additional utility endpoints
from rest_framework.views import APIView

class SiteStatsAPIView(APIView):
    """
    Get statistics for all sites
    """
    # permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get site statistics"""
        total_sites = Site.objects.count()
        published_sites = Site.objects.filter(published=True).count()
        total_visitors = Visitor.objects.count()
        
        # Get top 5 sites by visitor count
        top_sites = Site.objects.annotate(
            visitor_count=models.Count('visitor')
        ).order_by('-visitor_count')[:5]
        
        top_sites_data = []
        for site in top_sites:
            top_sites_data.append({
                'id': site.id,
                'name': site.name,
                'visitor_count': site.visitor_count
            })
        
        return Response({
            'total_sites': total_sites,
            'published_sites': published_sites,
            'unpublished_sites': total_sites - published_sites,
            'total_visitors': total_visitors,
            'top_sites': top_sites_data
        })


class VisitorStatsAPIView(APIView):
    """
    Get visitor statistics
    """
    # permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get visitor statistics"""
        from django.db.models import Count
        
        total_visitors = Visitor.objects.count()
        
        # Visitors by type
        visitor_types = Visitor.objects.values('visitorType').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Recent visitors (last 30 days)
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_visitors = Visitor.objects.filter(
            id__gte=thirty_days_ago  # Assuming auto-increment ID represents chronological order
        ).count()
        
        return Response({
            'total_visitors': total_visitors,
            'recent_visitors': recent_visitors,
            'visitor_types': list(visitor_types)
        })