from django.utils import timezone
from django.conf import settings
from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
import json
import uuid

from .models import Visitor, PageView, Session, Event
from .serializers import (
    VisitorSerializer,
    PageViewSerializer,
    SessionSerializer,
    EventSerializer,
    VisitorAnalyticsSerializer,
)

User = get_user_model()

class VisitorViewSet(viewsets.ModelViewSet):
    """ViewSet for visitor management"""
    queryset = Visitor.objects.all()
    serializer_class = VisitorSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Visitor.objects.all()
        return Visitor.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def track(self, request):
        """Track a new visitor or update existing visitor"""
        ip_address = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        referrer = request.META.get('HTTP_REFERER', '')

        # Try to find existing visitor
        visitor = Visitor.objects.filter(
            ip_address=ip_address,
            user_agent=user_agent
        ).first()

        if not visitor:
            # Create new visitor
            visitor = Visitor.objects.create(
                ip_address=ip_address,
                user_agent=user_agent,
                referrer=referrer,
                is_authenticated=request.user.is_authenticated
            )
            if request.user.is_authenticated:
                visitor.user = request.user
                visitor.save()

        # Update last visit
        visitor.last_visit = timezone.now()
        visitor.save()

        return Response(VisitorSerializer(visitor).data)

    @action(detail=True, methods=['post'])
    def update_location(self, request, pk=None):
        """Update visitor's location information"""
        visitor = self.get_object()
        serializer = self.get_serializer(visitor, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class PageViewViewSet(viewsets.ModelViewSet):
    """ViewSet for page view tracking"""
    queryset = PageView.objects.all()
    serializer_class = PageViewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return PageView.objects.all()
        return PageView.objects.filter(visitor__user=self.request.user)

    @action(detail=False, methods=['post'])
    def track(self, request):
        """Track a new page view"""
        visitor_id = request.data.get('visitor_id')
        url = request.data.get('url')
        path = request.data.get('path')
        title = request.data.get('title')
        duration = request.data.get('duration')

        try:
            visitor = Visitor.objects.get(id=visitor_id)
            page_view = PageView.objects.create(
                visitor=visitor,
                url=url,
                path=path,
                title=title,
                duration=duration
            )
            return Response(PageViewSerializer(page_view).data)
        except Visitor.DoesNotExist:
            return Response(
                {'error': 'Visitor not found'},
                status=status.HTTP_404_NOT_FOUND
            )

class SessionViewSet(viewsets.ModelViewSet):
    """ViewSet for session management"""
    queryset = Session.objects.all()
    serializer_class = SessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Session.objects.all()
        return Session.objects.filter(visitor__user=self.request.user)

    @action(detail=False, methods=['post'])
    def start(self, request):
        """Start a new session"""
        visitor_id = request.data.get('visitor_id')
        try:
            visitor = Visitor.objects.get(id=visitor_id)
            session = Session.objects.create(
                visitor=visitor,
                session_id=str(uuid.uuid4()),
                is_active=True
            )
            return Response(SessionSerializer(session).data)
        except Visitor.DoesNotExist:
            return Response(
                {'error': 'Visitor not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        """End an active session"""
        session = self.get_object()
        session.is_active = False
        session.end_time = timezone.now()
        session.save()
        return Response(SessionSerializer(session).data)

    @action(detail=True, methods=['post'])
    def add_page_view(self, request, pk=None):
        """Add a page view to the session"""
        session = self.get_object()
        page_view_id = request.data.get('page_view_id')
        try:
            page_view = PageView.objects.get(id=page_view_id)
            session.page_views.add(page_view)
            return Response(SessionSerializer(session).data)
        except PageView.DoesNotExist:
            return Response(
                {'error': 'Page view not found'},
                status=status.HTTP_404_NOT_FOUND
            )

class EventViewSet(viewsets.ModelViewSet):
    """ViewSet for event tracking"""
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Event.objects.all()
        return Event.objects.filter(visitor__user=self.request.user)

    @action(detail=False, methods=['post'])
    def track(self, request):
        """Track a new event"""
        visitor_id = request.data.get('visitor_id')
        session_id = request.data.get('session_id')
        event_type = request.data.get('event_type')
        element_id = request.data.get('element_id')
        element_class = request.data.get('element_class')
        element_text = request.data.get('element_text')
        metadata = request.data.get('metadata', {})

        try:
            visitor = Visitor.objects.get(id=visitor_id)
            session = Session.objects.get(id=session_id)
            event = Event.objects.create(
                visitor=visitor,
                session=session,
                event_type=event_type,
                element_id=element_id,
                element_class=element_class,
                element_text=element_text,
                metadata=metadata
            )
            return Response(EventSerializer(event).data)
        except (Visitor.DoesNotExist, Session.DoesNotExist):
            return Response(
                {'error': 'Visitor or Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )

class VisitorAnalyticsView(generics.RetrieveAPIView):
    """View for visitor analytics"""
    serializer_class = VisitorAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        visitor_id = self.kwargs.get('pk')
        try:
            visitor = Visitor.objects.get(id=visitor_id)
            if not self.request.user.is_staff and visitor.user != self.request.user:
                raise PermissionError("You don't have permission to view this visitor's analytics")
            return visitor
        except Visitor.DoesNotExist:
            raise Http404("Visitor not found")

    def get(self, request, *args, **kwargs):
        visitor = self.get_object()
        serializer = self.get_serializer(visitor)
        return Response(serializer.data) 