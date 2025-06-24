"""
Experiences Microservice Serializers
"""

from rest_framework import serializers
from django.db import transaction
from .models import (
    ExperienceCategory, Experience, ExperienceImage, ExperienceSession,
    ExperienceBooking, ParticipantDetail, ExperienceReview
)


class ExperienceCategorySerializer(serializers.ModelSerializer):
    """Serializer for experience categories"""
    
    subcategories = serializers.SerializerMethodField()
    
    class Meta:
        model = ExperienceCategory
        fields = ['id', 'name', 'slug', 'description', 'icon', 'parent', 'subcategories']
    
    def get_subcategories(self, obj):
        if obj.subcategories.exists():
            return ExperienceCategorySerializer(obj.subcategories.all(), many=True).data
        return []


class ExperienceImageSerializer(serializers.ModelSerializer):
    """Serializer for experience images"""
    
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ExperienceImage
        fields = [
            'id', 'image', 'image_url', 'caption', 'alt_text',
            'is_primary', 'order', 'created_at'
        ]
        read_only_fields = ['created_at']
    
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None


class ExperienceSessionSerializer(serializers.ModelSerializer):
    """Serializer for experience sessions"""
    
    available_spots_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = ExperienceSession
        fields = [
            'id', 'date', 'start_time', 'end_time', 'instructor_name',
            'instructor_bio', 'max_participants', 'available_spots',
            'booked_spots', 'price', 'status', 'notes',
            'available_spots_remaining'
        ]
    
    def get_available_spots_remaining(self, obj):
        return obj.available_spots - obj.booked_spots


class ExperienceListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for experience listings"""
    
    primary_image = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    next_session = serializers.SerializerMethodField()
    
    class Meta:
        model = Experience
        fields = [
            'id', 'title', 'slug', 'short_description', 'experience_type',
            'category_name', 'duration', 'base_price',
            'currency', 'average_rating', 'total_reviews', 'primary_image',
            'next_session', 'is_featured', 'difficulty_level'
        ]
    
    def get_primary_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(primary_image.image.url)
        return None
    
    def get_next_session(self, obj):
        from django.utils import timezone
        next_session = obj.sessions.filter(
            date__gte=timezone.now().date(),
            status='scheduled',
            available_spots__gt=0
        ).first()
        if next_session:
            return ExperienceSessionSerializer(next_session).data
        return None


class ExperienceDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for experience"""
    
    category = ExperienceCategorySerializer(read_only=True)
    images = ExperienceImageSerializer(many=True, read_only=True)
    sessions = ExperienceSessionSerializer(many=True, read_only=True)
    recent_reviews = serializers.SerializerMethodField()
    
    class Meta:
        model = Experience
        fields = [
            'id', 'title', 'slug', 'description', 'short_description',
            'experience_type', 'category', 'venue_name', 'address',
            'duration', 'min_participants', 'max_participants', 'age_restriction',
            'difficulty_level', 'base_price', 'currency', 'includes', 'excludes',
            'requirements', 'cancellation_policy', 'refund_policy',
            'average_rating', 'total_reviews', 'is_active', 'is_featured',
            'is_verified', 'requires_approval', 'meta_title', 'meta_description',
            'images', 'sessions', 'recent_reviews', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'average_rating', 'total_reviews']
    
    def get_recent_reviews(self, obj):
        recent_reviews = obj.reviews.filter(is_published=True)[:3]
        return ExperienceReviewSerializer(recent_reviews, many=True, context=self.context).data


class ParticipantDetailSerializer(serializers.ModelSerializer):
    """Serializer for participant details"""
    
    class Meta:
        model = ParticipantDetail
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone',
            'date_of_birth', 'gender', 'emergency_contact_name',
            'emergency_contact_phone', 'dietary_requirements',
            'medical_conditions', 'accessibility_needs'
        ]


class ExperienceBookingSerializer(serializers.ModelSerializer):
    """Serializer for experience bookings"""
    
    session_info = ExperienceSessionSerializer(source='session', read_only=True)
    participants = ParticipantDetailSerializer(many=True, required=False)
    
    class Meta:
        model = ExperienceBooking
        fields = [
            'id', 'booking_reference', 'session', 'session_info',
            'customer_name', 'customer_email', 'customer_phone',
            'number_of_participants', 'unit_price', 'subtotal',
            'taxes', 'fees', 'total_amount', 'currency', 'status',
            'payment_status', 'special_requests', 'dietary_requirements',
            'accessibility_needs', 'booking_date', 'confirmation_date',
            'participants'
        ]
        read_only_fields = [
            'booking_reference', 'subtotal', 'total_amount',
            'booking_date', 'confirmation_date'
        ]
    
    @transaction.atomic
    def create(self, validated_data):
        participants_data = validated_data.pop('participants', [])
        booking = super().create(validated_data)
        
        # Create participant details
        for participant_data in participants_data:
            ParticipantDetail.objects.create(booking=booking, **participant_data)
        
        return booking


class ExperienceReviewSerializer(serializers.ModelSerializer):
    """Serializer for experience reviews"""
    
    experience_title = serializers.CharField(source='experience.title', read_only=True)
    
    class Meta:
        model = ExperienceReview
        fields = [
            'id', 'experience', 'experience_title', 'reviewer_name',
            'rating', 'title', 'comment', 'organization_rating',
            'instructor_rating', 'venue_rating', 'value_rating',
            'is_verified', 'is_published', 'response', 'response_date',
            'created_at'
        ]
        read_only_fields = ['created_at', 'is_verified', 'response', 'response_date']
