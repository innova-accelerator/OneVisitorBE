from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction, models
from django.db.models import Q, Count
from .models import Site, Host, Visitor, visitorPhoto
from .serializers import (
    SiteListSerializer, SiteDetailSerializer, SiteCreateUpdateSerializer,
    HostListSerializer, HostDetailSerializer, HostCreateUpdateSerializer,
    HostWithVisitorsSerializer, HostChoiceSerializer,
    VisitorListSerializer, VisitorDetailSerializer, VisitorCreateSerializer,
    VisitorPhotoSerializer, SiteWithHostsAndVisitorsSerializer
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
        queryset = Site.objects.prefetch_related('host', 'visitor')
        
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
        """Create a new site with hosts"""
        # Extract hosts data from request
        hosts_data = request.data.pop('host', [])  # Remove 'host' from site data
        
        # Create the site first
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            site = serializer.save()
            
            # Create hosts for this site
            created_hosts = []
            for host_data in hosts_data:
                # Remove the temporary ID if it exists
                host_data.pop('id', None)
                # Add the site reference
                host_data['site'] = site.id
                
                host_serializer = HostCreateUpdateSerializer(data=host_data)
                if host_serializer.is_valid():
                    host = host_serializer.save()
                    created_hosts.append(host)
                else:
                    # If host creation fails, log the error but continue
                    print(f"Host creation failed: {host_serializer.errors}")
        
        # Return detailed response with created hosts
        response_serializer = SiteDetailSerializer(site)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Update site with hosts (PUT/PATCH)"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Extract hosts data from request
        hosts_data = request.data.pop('host', [])
        
        # Update the site
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            site = serializer.save()
            
            # Handle hosts update
            if hosts_data:  # Only update hosts if provided
                # Get existing hosts
                existing_hosts = {str(host.id): host for host in site.host.all()}
                updated_host_ids = set()
                
                for host_data in hosts_data:
                    host_id = host_data.get('id')
                    
                    # Remove temporary IDs that start with 'host-'
                    if host_id and str(host_id).startswith('host-'):
                        host_data.pop('id', None)
                        host_id = None
                    
                    if host_id and str(host_id) in existing_hosts:
                        # Update existing host
                        host = existing_hosts[str(host_id)]
                        host_serializer = HostCreateUpdateSerializer(host, data=host_data, partial=True)
                        if host_serializer.is_valid():
                            host_serializer.save()
                            updated_host_ids.add(str(host_id))
                    else:
                        # Create new host
                        host_data['site'] = site.id
                        host_serializer = HostCreateUpdateSerializer(data=host_data)
                        if host_serializer.is_valid():
                            new_host = host_serializer.save()
                            updated_host_ids.add(str(new_host.id))
                
                # Delete hosts that weren't in the update
                for host_id, host in existing_hosts.items():
                    if host_id not in updated_host_ids:
                        host.delete()
        
        # Return detailed response
        response_serializer = SiteDetailSerializer(site)
        return Response(response_serializer.data)
    
    @action(detail=True, methods=['get'])
    def hosts(self, request, pk=None):
        """Get all hosts for a specific site"""
        site = self.get_object()
        hosts = site.host.all().order_by('-id')
        
        # Pagination
        page = self.paginate_queryset(hosts)
        if page is not None:
            serializer = HostListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = HostListSerializer(hosts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def visitors(self, request, pk=None):
        """Get all visitors for a specific site"""
        site = self.get_object()
        visitors = site.visitor.select_related('host').prefetch_related('visitorPhoto').order_by('-id')
        
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
        site.save()  # The model's save() method will handle lastPublished automatically
        
        serializer = SiteDetailSerializer(site)
        return Response({
            'message': f'Site {"published" if site.published else "unpublished"} successfully',
            'data': serializer.data
        })


class HostViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Host model
    """
    queryset = Host.objects.all()
    # permission_classes = [IsAuthenticated]  # Uncomment if authentication required
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return HostListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return HostCreateUpdateSerializer
        else:
            return HostDetailSerializer
    
    def get_queryset(self):
        """Filter hosts based on query parameters"""
        queryset = Host.objects.select_related('site').prefetch_related('visitor')
        
        # Filter by site
        site_id = self.request.query_params.get('site', None)
        if site_id is not None:
            queryset = queryset.filter(site_id=site_id)
        
        # Filter by department
        department = self.request.query_params.get('department', None)
        if department is not None:
            queryset = queryset.filter(department__icontains=department)
        
        # Search by name or email
        search = self.request.query_params.get('search', None)
        if search is not None:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(email__icontains=search) |
                Q(department__icontains=search)
            )
        
        return queryset.order_by('-id')
    
    def create(self, request, *args, **kwargs):
        """Create a new host"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        host = serializer.save()
        
        # Return detailed response
        response_serializer = HostDetailSerializer(host)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Update host (PUT/PATCH)"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        host = serializer.save()
        
        # Return detailed response
        response_serializer = HostDetailSerializer(host)
        return Response(response_serializer.data)
    
    @action(detail=True, methods=['get'])
    def visitors(self, request, pk=None):
        """Get all visitors for a specific host"""
        host = self.get_object()
        visitors = host.visitor.select_related('site').prefetch_related('visitorPhoto').order_by('-id')
        
        # Pagination
        page = self.paginate_queryset(visitors)
        if page is not None:
            serializer = VisitorListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = VisitorListSerializer(visitors, many=True)
        return Response(serializer.data)


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
        queryset = Visitor.objects.select_related('site', 'host').prefetch_related('visitorPhoto')
        
        # Filter by site
        site_id = self.request.query_params.get('site', None)
        if site_id is not None:
            queryset = queryset.filter(site_id=site_id)
        
        # Filter by host
        host_id = self.request.query_params.get('host', None)
        if host_id is not None:
            queryset = queryset.filter(host_id=host_id)
        
        # Filter by visitor type
        visitor_type = self.request.query_params.get('visitorType', None)
        if visitor_type is not None:
            queryset = queryset.filter(visitorType=visitor_type)
        
        # Search by name, email, or company
        search = self.request.query_params.get('search', None)
        if search is not None:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(email__icontains=search) |
                Q(company__icontains=search)
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
        total_hosts = Host.objects.count()
        
        # Get top 5 sites by visitor count
        top_sites = Site.objects.annotate(
            visitor_count=Count('visitor'),
            host_count=Count('host')
        ).order_by('-visitor_count')[:5]
        
        top_sites_data = []
        for site in top_sites:
            top_sites_data.append({
                'id': site.id,
                'name': site.name,
                'visitor_count': site.visitor_count,
                'host_count': site.host_count
            })
        
        return Response({
            'total_sites': total_sites,
            'published_sites': published_sites,
            'unpublished_sites': total_sites - published_sites,
            'total_visitors': total_visitors,
            'total_hosts': total_hosts,
            'top_sites': top_sites_data
        })


class HostStatsAPIView(APIView):
    """
    Get host statistics
    """
    # permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get host statistics"""
        total_hosts = Host.objects.count()
        
        # Hosts by department
        departments = Host.objects.values('department').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Top hosts by visitor count
        top_hosts = Host.objects.annotate(
            visitor_count=Count('visitor')
        ).order_by('-visitor_count')[:5]
        
        top_hosts_data = []
        for host in top_hosts:
            top_hosts_data.append({
                'id': host.id,
                'name': host.name,
                'department': host.department,
                'visitor_count': host.visitor_count
            })
        
        return Response({
            'total_hosts': total_hosts,
            'departments': list(departments),
            'top_hosts': top_hosts_data
        })


class VisitorStatsAPIView(APIView):
    """
    Get visitor statistics
    """
    # permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get visitor statistics"""
        total_visitors = Visitor.objects.count()
        
        # Visitors by type
        visitor_types = Visitor.objects.values('visitorType').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Recent visitors (last 30 days) - using ID as proxy for recent
        # You might want to add a created_at field for better date filtering
        recent_visitors_count = Visitor.objects.order_by('-id')[:30].count()
        
        # Visitors by site
        visitors_by_site = Site.objects.annotate(
            visitor_count=Count('visitor')
        ).values('id', 'name', 'visitor_count').order_by('-visitor_count')
        
        return Response({
            'total_visitors': total_visitors,
            'recent_visitors': recent_visitors_count,
            'visitor_types': list(visitor_types),
            'visitors_by_site': list(visitors_by_site)
        })


class HostChoicesAPIView(APIView):
    """
    Get host choices for a specific site (for dropdowns)
    """
    def get(self, request):
        """Get hosts filtered by site"""
        site_id = request.query_params.get('site', None)
        
        if site_id:
            hosts = Host.objects.filter(site_id=site_id)
        else:
            hosts = Host.objects.all()
        
        serializer = HostChoiceSerializer(hosts, many=True)
        return Response(serializer.data)


class SiteChoicesAPIView(APIView):
    """
    Get site choices (for dropdowns)
    """
    def get(self, request):
        """Get all sites for dropdown"""
        sites = Site.objects.all().order_by('name')
        serializer = SiteChoiceSerializer(sites, many=True)
        return Response(serializer.data)