import django_filters
from django.db import models
from .models import Experience, ExperienceBooking, ExperienceReview, ExperienceSession

class ExperienceFilter(django_filters.FilterSet):
    # Basic filters
    name = django_filters.CharFilter(lookup_expr='icontains')
    category = django_filters.CharFilter(field_name='category__name', lookup_expr='icontains')
    location = django_filters.CharFilter(lookup_expr='icontains')
    
    # Price range filters
    min_price = django_filters.NumberFilter(field_name='price_per_person', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price_per_person', lookup_expr='lte')
    price_range = django_filters.RangeFilter(field_name='price_per_person')
    
    # Duration filters
    min_duration = django_filters.NumberFilter(field_name='duration_hours', lookup_expr='gte')
    max_duration = django_filters.NumberFilter(field_name='duration_hours', lookup_expr='lte')
    duration_range = django_filters.RangeFilter(field_name='duration_hours')
    
    # Capacity filters
    min_capacity = django_filters.NumberFilter(field_name='max_participants', lookup_expr='gte')
    max_capacity = django_filters.NumberFilter(field_name='max_participants', lookup_expr='lte')
    
    # Rating filter
    min_rating = django_filters.NumberFilter(field_name='average_rating', lookup_expr='gte')
    
    # Boolean filters
    is_active = django_filters.BooleanFilter()
    requires_booking = django_filters.BooleanFilter()
    is_outdoor = django_filters.BooleanFilter()
    is_family_friendly = django_filters.BooleanFilter()
    
    # Date availability filters
    available_from = django_filters.DateFilter(method='filter_available_from')
    available_to = django_filters.DateFilter(method='filter_available_to')
    
    # Advanced filters
    difficulty_level = django_filters.ChoiceFilter(choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ])
    
    age_group = django_filters.ChoiceFilter(choices=[
        ('kids', 'Kids (0-12)'),
        ('teens', 'Teens (13-17)'),
        ('adults', 'Adults (18-64)'),
        ('seniors', 'Seniors (65+)'),
        ('all_ages', 'All Ages'),
    ])
    
    # Search filter
    search = django_filters.CharFilter(method='filter_search')
    
    # Ordering
    ordering = django_filters.OrderingFilter(
        fields=(
            ('name', 'name'),
            ('price_per_person', 'price'),
            ('average_rating', 'rating'),
            ('duration_hours', 'duration'),
            ('created_at', 'created'),
            ('updated_at', 'updated'),
        ),
        field_labels={
            'name': 'Name',
            'price_per_person': 'Price',
            'average_rating': 'Rating',
            'duration_hours': 'Duration',
            'created_at': 'Date Created',
            'updated_at': 'Date Updated',
        }
    )

    class Meta:
        model = Experience
        fields = [
            'name', 'category', 'location', 'min_price', 'max_price',
            'min_duration', 'max_duration', 'min_capacity', 'max_capacity',
            'min_rating', 'is_active', 'requires_booking', 'is_outdoor',
            'is_family_friendly', 'difficulty_level', 'age_group'
        ]

    def filter_available_from(self, queryset, name, value):
        """Filter experiences that have sessions available from a specific date"""
        return queryset.filter(
            sessions__date__gte=value,
            sessions__is_available=True
        ).distinct()

    def filter_available_to(self, queryset, name, value):
        """Filter experiences that have sessions available until a specific date"""
        return queryset.filter(
            sessions__date__lte=value,
            sessions__is_available=True
        ).distinct()

    def filter_search(self, queryset, name, value):
        """Search across multiple fields"""
        return queryset.filter(
            models.Q(name__icontains=value) |
            models.Q(description__icontains=value) |
            models.Q(location__icontains=value) |
            models.Q(category__name__icontains=value) |
            models.Q(tags__icontains=value)
        ).distinct()


class ExperienceBookingFilter(django_filters.FilterSet):
    # Date filters
    booking_date = django_filters.DateFilter(field_name='session__date')
    booking_date_from = django_filters.DateFilter(field_name='session__date', lookup_expr='gte')
    booking_date_to = django_filters.DateFilter(field_name='session__date', lookup_expr='lte')
    booking_date_range = django_filters.DateFromToRangeFilter(field_name='session__date')
    
    # Created date filters
    created_from = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_to = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    created_range = django_filters.DateFromToRangeFilter(field_name='created_at')
    
    # Status filters
    status = django_filters.ChoiceFilter(choices=[
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('no_show', 'No Show'),
    ])
    
    # Experience filters
    experience = django_filters.ModelChoiceFilter(
        field_name='session__experience',
        queryset=Experience.objects.all()
    )
    experience_name = django_filters.CharFilter(
        field_name='session__experience__name',
        lookup_expr='icontains'
    )
    experience_category = django_filters.CharFilter(
        field_name='session__experience__category__name',
        lookup_expr='icontains'
    )
    
    # Price filters
    min_total_price = django_filters.NumberFilter(field_name='total_price', lookup_expr='gte')
    max_total_price = django_filters.NumberFilter(field_name='total_price', lookup_expr='lte')
    price_range = django_filters.RangeFilter(field_name='total_price')
    
    # Participant filters
    min_participants = django_filters.NumberFilter(field_name='number_of_participants', lookup_expr='gte')
    max_participants = django_filters.NumberFilter(field_name='number_of_participants', lookup_expr='lte')
    
    # Boolean filters
    is_paid = django_filters.BooleanFilter()
    requires_confirmation = django_filters.BooleanFilter(field_name='session__experience__requires_booking')
    
    # Customer filters (for provider view)
    customer_name = django_filters.CharFilter(field_name='customer__first_name', lookup_expr='icontains')
    customer_email = django_filters.CharFilter(field_name='customer__email', lookup_expr='icontains')
    
    # Ordering
    ordering = django_filters.OrderingFilter(
        fields=(
            ('created_at', 'created'),
            ('session__date', 'booking_date'),
            ('total_price', 'price'),
            ('number_of_participants', 'participants'),
            ('status', 'status'),
        ),
        field_labels={
            'created_at': 'Date Created',
            'session__date': 'Booking Date',
            'total_price': 'Total Price',
            'number_of_participants': 'Participants',
            'status': 'Status',
        }
    )

    class Meta:
        model = ExperienceBooking
        fields = [
            'status', 'is_paid', 'booking_date', 'experience',
            'min_total_price', 'max_total_price', 'min_participants', 'max_participants'
        ]


class ExperienceReviewFilter(django_filters.FilterSet):
    # Rating filters
    rating = django_filters.NumberFilter()
    min_rating = django_filters.NumberFilter(field_name='rating', lookup_expr='gte')
    max_rating = django_filters.NumberFilter(field_name='rating', lookup_expr='lte')
    rating_range = django_filters.RangeFilter(field_name='rating')
    
    # Date filters
    created_from = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_to = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    created_range = django_filters.DateFromToRangeFilter(field_name='created_at')
    
    # Experience filters
    experience = django_filters.ModelChoiceFilter(queryset=Experience.objects.all())
    experience_name = django_filters.CharFilter(
        field_name='experience__name',
        lookup_expr='icontains'
    )
    
    # Content filters
    has_comment = django_filters.BooleanFilter(method='filter_has_comment')
    search = django_filters.CharFilter(method='filter_search')
    
    # Ordering
    ordering = django_filters.OrderingFilter(
        fields=(
            ('created_at', 'created'),
            ('rating', 'rating'),
            ('experience__name', 'experience'),
        ),
        field_labels={
            'created_at': 'Date Created',
            'rating': 'Rating',
            'experience__name': 'Experience',
        }
    )

    class Meta:
        model = ExperienceReview
        fields = ['rating', 'experience']

    def filter_has_comment(self, queryset, name, value):
        """Filter reviews that have comments"""
        if value:
            return queryset.exclude(comment__isnull=True).exclude(comment__exact='')
        return queryset.filter(models.Q(comment__isnull=True) | models.Q(comment__exact=''))

    def filter_search(self, queryset, name, value):
        """Search in review comments"""
        return queryset.filter(comment__icontains=value)


class ExperienceSessionFilter(django_filters.FilterSet):
    # Date filters
    date = django_filters.DateFilter()
    date_from = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='date', lookup_expr='lte')
    date_range = django_filters.DateFromToRangeFilter(field_name='date')
    
    # Time filters
    start_time = django_filters.TimeFilter()
    start_time_from = django_filters.TimeFilter(field_name='start_time', lookup_expr='gte')
    start_time_to = django_filters.TimeFilter(field_name='start_time', lookup_expr='lte')
    
    # Experience filters
    experience = django_filters.ModelChoiceFilter(queryset=Experience.objects.all())
    experience_name = django_filters.CharFilter(
        field_name='experience__name',
        lookup_expr='icontains'
    )
    
    # Availability filters
    is_available = django_filters.BooleanFilter()
    has_capacity = django_filters.BooleanFilter(method='filter_has_capacity')
    min_available_spots = django_filters.NumberFilter(method='filter_min_available_spots')
    
    # Booking filters
    has_bookings = django_filters.BooleanFilter(method='filter_has_bookings')
    
    # Ordering
    ordering = django_filters.OrderingFilter(
        fields=(
            ('date', 'date'),
            ('start_time', 'start_time'),
            ('experience__name', 'experience'),
            ('available_spots', 'available_spots'),
        ),
        field_labels={
            'date': 'Date',
            'start_time': 'Start Time',
            'experience__name': 'Experience',
            'available_spots': 'Available Spots',
        }
    )

    class Meta:
        model = ExperienceSession
        fields = ['date', 'experience', 'is_available']

    def filter_has_capacity(self, queryset, name, value):
        """Filter sessions that have available capacity"""
        if value:
            return queryset.filter(available_spots__gt=0)
        return queryset.filter(available_spots=0)

    def filter_min_available_spots(self, queryset, name, value):
        """Filter sessions with minimum available spots"""
        return queryset.filter(available_spots__gte=value)

    def filter_has_bookings(self, queryset, name, value):
        """Filter sessions that have bookings"""
        if value:
            return queryset.filter(bookings__isnull=False).distinct()
        return queryset.filter(bookings__isnull=True)
