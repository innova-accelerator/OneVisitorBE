from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Visitor, Session, PageView, Event
from .serializers import (
    VisitorSerializer, SessionSerializer,
    PageViewSerializer, EventSerializer
)

class VisitorViewSet(viewsets.ModelViewSet):
    queryset = Visitor.objects.all()
    serializer_class = VisitorSerializer

    @action(detail=True, methods=['post'])
    def update_location(self, request, pk=None):
        visitor = self.get_object()
        visitor.country = request.data.get('country')
        visitor.city = request.data.get('city')
        visitor.save()
        return Response(self.get_serializer(visitor).data)

    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        visitor = self.get_object()

        return Response({...})

    @action(detail=True, methods=['get'])
    def journey(self, request, pk=None):
        visitor = self.get_object()

        return Response({...})

class SessionViewSet(viewsets.ModelViewSet):
    queryset = Session.objects.all()
    serializer_class = SessionSerializer

    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        session = self.get_object()

        return Response(self.get_serializer(session).data)

class PageViewViewSet(viewsets.ModelViewSet):
    queryset = PageView.objects.all()
    serializer_class = PageViewSerializer

    @action(detail=False, methods=['get'])
    def aggregate(self, request):

        return Response({...})

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    @action(detail=False, methods=['get'])
    def aggregate(self, request):
    	
        return Response({...})