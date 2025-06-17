"""
Experiences Microservice Views
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime

from .models import (
    ExperienceCategory, Experience, ExperienceSession,
    ExperienceBooking, ExperienceReview
)
from .serializers import (
    ExperienceCategorySerializer, ExperienceListSerializer,
    ExperienceDetailSerializer, ExperienceSessionSerializer,
    ExperienceBookingSerializer, ExperienceReviewSerializer
)
from .filters import ExperienceFilter, ExperienceBookingFilter
from .permissions import IsOwnerOrReadOnly, IsProfileMember


class ExperienceCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for experience categories"""
    
    queryset = ExperienceCategory.objects.filter(parent=None)
    serializer_class = ExperienceCategorySerializer
    filter_backends = [filters.OrderingFilter]
    ordering = ['name']


class ExperienceViewSet(viewsets.ModelViewSet):
    """ViewSet for experience management"""
    
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ExperienceFilter
    search_fields = ['title', 'description', 'city', 'venue_name']
    ordering_fields = ['created_at', 'average_rating', 'base_price', 'title']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Experience.objects.select_related('category').prefetch_related(
            'images', 'sessions'
        )
        
        if self.request.user.is_authenticated:
            profile_id = self.request.headers.get('X-Profile-ID')
            if profile_id and self.action in ['create', 'update', 'partial_update', 'destroy']:
                queryset = queryset.filter(profile_id=profile_id)
        
        if self.action in ['list', 'retrieve']:
            queryset = queryset.filter(is_active=True)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ExperienceListSerializer
        return ExperienceDetailSerializer
    
    def perform_create(self, serializer):
        profile_id = self.request.headers.get('X-Profile-ID')
        user_id = str(self.request.user.id)
        serializer.save(
            profile_id=profile_id,
            created_by_id=user_id
        )
    
    @action(detail=True, methods=['get'])
    def sessions(self, request, pk=None):
        """Get sessions for an experience"""
        experience = self.get_object()
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        sessions = experience.sessions.filter(
            status='scheduled',
            date__gte=timezone.now().date()
        )
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                sessions = sessions.filter(date__gte=date_from_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                sessions = sessions.filter(date__lte=date_to_obj)
            except ValueError:
                pass
        
        serializer = ExperienceSessionSerializer(sessions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured experiences"""
        featured = self.get_queryset().filter(is_featured=True)[:10]
        serializer = ExperienceListSerializer(featured, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced search for experiences"""
        queryset = self.get_queryset()
        
        # Location search
        city = request.query_params.get('city')
        if city:
            queryset = queryset.filter(city__icontains=city)
        
        # Date availability
        date = request.query_params.get('date')
        if date:
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d').date()
                queryset = queryset.filter(
                    sessions__date=date_obj,
                    sessions__status='scheduled',
                    sessions__available_spots__gt=0
                ).distinct()
            except ValueError:
                pass
        
        # Price range
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(base_price__gte=min_price)
        if max_price:
            queryset = queryset.filter(base_price__lte=max_price)
        
        # Category
        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
        
        # Experience type
        experience_type = request.query_params.get('type')
        if experience_type:
            queryset = queryset.filter(experience_type=experience_type)
        
        # Difficulty level
        difficulty = request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty_level=difficulty)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ExperienceListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ExperienceListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)


class ExperienceSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for experience session management"""
    
    serializer_class = ExperienceSessionSerializer
    permission_classes = [IsAuthenticated, IsProfileMember]
    filter_backends = [filters.OrderingFilter]
    ordering = ['date', 'start_time']
    
    def get_queryset(self):
        profile_id = self.request.headers.get('X-Profile-ID')
        return ExperienceSession.objects.filter(
            profile_id=profile_id
        ).select_related('experience')
    
    def perform_create(self, serializer):
        profile_id = self.request.headers.get('X-Profile-ID')
        user_id = str(self.request.user.id)
        serializer.save(
            profile_id=profile_id,
            created_by_id=user_id
        )


class ExperienceBookingViewSet(viewsets.ModelViewSet):
    """ViewSet for experience bookings"""
    
    serializer_class = ExperienceBookingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ExperienceBookingFilter
    ordering = ['-booking_date']
    
    def get_queryset(self):
        user_id = str(self.request.user.id)
        profile_id = self.request.headers.get('X-Profile-ID')
        
        queryset = ExperienceBooking.objects.select_related(
            'session__experience'
        )
        
        if profile_id:
            return queryset.filter(
                Q(customer_user_id=user_id) | Q(profile_id=profile_id)
            )
        else:
            return queryset.filter(customer_user_id=user_id)
    
    def perform_create(self, serializer):
        user_id = str(self.request.user.id)
        profile_id = self.request.headers.get('X-Profile-ID')
        serializer.save(
            customer_user_id=user_id,
            profile_id=profile_id or 'customer',
            created_by_id=user_id
        )
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm a booking"""
        booking = self.get_object()
        if booking.status != 'pending':
            return Response(
                {'error': 'Only pending bookings can be confirmed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'confirmed'
        booking.confirmation_date = timezone.now()
        booking.save()
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a booking"""
        booking = self.get_object()
        if booking.status in ['completed', 'cancelled']:
            return Response(
                {'error': 'Cannot cancel completed or already cancelled booking'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'cancelled'
        booking.cancellation_date = timezone.now()
        booking.save()
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)


class ExperienceReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for experience reviews"""
    
    serializer_class = ExperienceReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering = ['-created_at']
    
    def get_queryset(self):
        user_id = str(self.request.user.id)
        profile_id = self.request.headers.get('X-Profile-ID')
        
        queryset = ExperienceReview.objects.select_related('experience', 'booking')
        
        if profile_id:
            return queryset.filter(
                Q(reviewer_user_id=user_id) | Q(profile_id=profile_id)
            )
        else:
            return queryset.filter(reviewer_user_id=user_id)
    
    def perform_create(self, serializer):
        user_id = str(self.request.user.id)
        profile_id = self.request.headers.get('X-Profile-ID')
        serializer.save(
            reviewer_user_id=user_id,
            reviewer_name=self.request.user.get_full_name() or self.request.user.email,
            profile_id=profile_id or 'customer',
            created_by_id=user_id
        )
