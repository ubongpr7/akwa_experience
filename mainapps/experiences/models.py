"""
Experiences Microservice Models
Handles tours, activities, events, classes (fitness, music, art) bookings
"""

import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from mptt.models import MPTTModel

class Address(models.Model):
    
    country = models.CharField(
        max_length=255,
        verbose_name=_('Country'),
        help_text=_('Country of the address'),
        null=True,
        blank=True
    )
    region = models.CharField(
        max_length=255,
        verbose_name=_('Region/State'),
        help_text=_('Region or state within the country'),
        null=True,
        blank=True
    )
    subregion = models.CharField(
        max_length=255,
        verbose_name=_('Subregion/Province'),
        help_text=_('Subregion or province within the region'),
        null=True,
        blank=True
    )
    city = models.CharField(
        max_length=255,
        verbose_name=_('City'),
        help_text=_('City of the address'),
        null=True,
        blank=True
    )
    apt_number = models.PositiveIntegerField(
        verbose_name=_('Apartment number'),
        null=True,
        blank=True
    )
    street_number = models.PositiveIntegerField(
        verbose_name=_('Street number'),
        null=True,
        blank=True
    )
    street = models.CharField(max_length=255,blank=False,null=True)

    postal_code = models.CharField(
        max_length=10,
        verbose_name=_('Postal code'),
        help_text=_('Postal code'),
        blank=True,
        null=True,
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name=_('Latitude'),
        help_text=_('Geographical latitude of the address'),
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name=_('Longitude'),
        help_text=_('Geographical longitude of the address'),
        null=True,
        blank=True
    )

    def __str__(self):
        return f'{self.street}, {self.city}, {self.region}, {self.country}'

class ExperienceManager(models.Manager):
    """Custom manager for experience-related models"""
    
    def for_profile(self, profile_id):
        return self.get_queryset().filter(profile_id=profile_id)
    
    def active(self):
        return self.get_queryset().filter(is_active=True)
    
    def available_for_date(self, date):
        return self.get_queryset().filter(
            sessions__date=date,
            sessions__available_spots__gt=0,
            is_active=True
        ).distinct()


class ProfileMixin(models.Model):
    """Abstract model providing multi-tenant functionality"""
    
    profile_id = models.CharField(
        max_length=50,
        help_text="Reference to CompanyProfile ID from users service"
    )
    created_by_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Reference to User ID from users service"
    )
    modified_by_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Reference to User ID from users service"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = ExperienceManager()
    
    class Meta:
        abstract = True


class ExperienceType(models.TextChoices):
    TOUR = 'tour', _('Tour')
    ACTIVITY = 'activity', _('Activity')
    EVENT = 'event', _('Event')
    FITNESS_CLASS = 'fitness_class', _('Fitness Class')
    MUSIC_CLASS = 'music_class', _('Music Class')
    ART_CLASS = 'art_class', _('Art Class')
    WORKSHOP = 'workshop', _('Workshop')
    SEMINAR = 'seminar', _('Seminar')
    CONFERENCE = 'conference', _('Conference')
    CONCERT = 'concert', _('Concert')
    SPORTS_EVENT = 'sports_event', _('Sports Event')
    CULTURAL_EVENT = 'cultural_event', _('Cultural Event')

class ExperienceCategory(MPTTModel):
    """Categories for organizing experiences"""
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    
    class Meta:
        verbose_name_plural = "Experience Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Experience(ProfileMixin):
    """Main experience model"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=500, blank=True)
    
    experience_type = models.CharField(
        max_length=20,
        choices=ExperienceType.choices
    )
    category = models.ForeignKey(
        ExperienceCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='experiences'
    )
    
    # Location Information
    venue_name = models.CharField(max_length=255, blank=True)
    address = models.ForeignKey(
        Address,
        null=True,
        blank=True,
        on_delete= models.SET_NULL
    )
    # Experience Details
    duration = models.DurationField(help_text="Duration of the experience")
    min_participants = models.PositiveIntegerField(default=1)
    max_participants = models.PositiveIntegerField()
    age_restriction = models.CharField(max_length=100, blank=True)
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', _('Beginner')),
            ('intermediate', _('Intermediate')),
            ('advanced', _('Advanced')),
            ('all_levels', _('All Levels')),
        ],
        default='all_levels'
    )
    
    # Pricing
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, null=True, blank=True)
    
    # What's included/excluded
    includes = models.TextField(blank=True, help_text="What's included in the experience")
    excludes = models.TextField(blank=True, help_text="What's not included")
    requirements = models.TextField(blank=True, help_text="Requirements for participants")
    
    # Cancellation policy
    cancellation_policy = models.TextField(blank=True)
    refund_policy = models.TextField(blank=True)
    
    # Ratings and Reviews
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    total_reviews = models.PositiveIntegerField(default=0)
    
    # Status flags
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    requires_approval = models.BooleanField(default=False)
    
    # SEO
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.CharField(max_length=500, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['profile_id', 'is_active']),
            models.Index(fields=['experience_type', 'category']),
            models.Index(fields=['is_active', 'is_featured']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.city}"


class ExperienceImage(ProfileMixin):
    """Images for experiences"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    experience = models.ForeignKey(
        Experience,
        on_delete=models.CASCADE,
        related_name='images'
    )
    
    image = models.ImageField(upload_to='experiences/%Y/%m/%d/')
    video = models.FileField(
        upload_to='experiences/videos/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text="Optional video file for the experience"
    )
    caption = models.CharField(max_length=255, blank=True)
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'created_at']


class ExperienceSession(ProfileMixin):
    """Scheduled sessions for experiences"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    experience = models.ForeignKey(
        Experience,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    
    # Session timing
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Instructor/Guide information
    instructor_name = models.CharField(max_length=255, blank=True)
    instructor_bio = models.TextField(blank=True)
    instructor_user_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="Reference to User ID from users service"
    )
    
    # Availability
    max_participants = models.PositiveIntegerField()
    available_spots = models.PositiveIntegerField()
    booked_spots = models.PositiveIntegerField(default=0)
    
    # Pricing (can override experience base price)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('scheduled', _('Scheduled')),
            ('confirmed', _('Confirmed')),
            ('in_progress', _('In Progress')),
            ('completed', _('Completed')),
            ('cancelled', _('Cancelled')),
            ('postponed', _('Postponed')),
        ],
        default='scheduled'
    )
    
    # Special notes
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['date', 'start_time']
        indexes = [
            models.Index(fields=['experience', 'date']),
            models.Index(fields=['date', 'status']),
        ]
    
    def __str__(self):
        return f"{self.experience.title} - {self.date} {self.start_time}"


class BookingStatus(models.TextChoices):
    PENDING = 'pending', _('Pending')
    CONFIRMED = 'confirmed', _('Confirmed')
    CHECKED_IN = 'checked_in', _('Checked In')
    ATTENDED = 'attended', _('Attended')
    COMPLETED = 'completed', _('Completed')
    CANCELLED = 'cancelled', _('Cancelled')
    NO_SHOW = 'no_show', _('No Show')


class ExperienceBooking(ProfileMixin):
    """Booking records for experiences"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking_reference = models.CharField(max_length=20, unique=True)
    
    # Experience details
    session = models.ForeignKey(
        ExperienceSession,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    
    # Customer information (references to users service)
    customer_user_id = models.CharField(
        max_length=50,
        help_text="Reference to User ID from users service"
    )
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    
    # Booking details
    number_of_participants = models.PositiveIntegerField(default=1)
    
    # Pricing
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    taxes = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='NGN')
    
    # Status and tracking
    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING
    )
    
    # Payment information (references to payment service)
    payment_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Reference to payment record in payment service"
    )
    payment_status = models.CharField(max_length=20, default='pending')
    
    # Special requests and notes
    special_requests = models.TextField(blank=True)
    dietary_requirements = models.TextField(blank=True)
    accessibility_needs = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    
    # Timestamps
    booking_date = models.DateTimeField(default=timezone.now)
    confirmation_date = models.DateTimeField(null=True, blank=True)
    check_in_time = models.DateTimeField(null=True, blank=True)
    completion_time = models.DateTimeField(null=True, blank=True)
    cancellation_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-booking_date']
        indexes = [
            models.Index(fields=['profile_id', 'status']),
            models.Index(fields=['customer_user_id']),
            models.Index(fields=['session']),
            models.Index(fields=['booking_reference']),
        ]
    
    def __str__(self):
        return f"Booking {self.booking_reference} - {self.session.experience.title}"
    
    def save(self, *args, **kwargs):
        if not self.booking_reference:
            self.booking_reference = self.generate_booking_reference()
        
        # Calculate totals
        self.subtotal = self.unit_price * self.number_of_participants
        self.total_amount = self.subtotal + self.taxes + self.fees
        
        super().save(*args, **kwargs)
    
    def generate_booking_reference(self):
        """Generate unique booking reference"""
        import random
        import string
        
        prefix = "EXP"
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return f"{prefix}-{self.profile_id}-{suffix}"


class ParticipantDetail(models.Model):
    """Individual participant details for experience bookings"""
    
    booking = models.ForeignKey(
        ExperienceBooking,
        on_delete=models.CASCADE,
        related_name='participants'
    )
    
    # Participant Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        blank=True,
    )
    
    # Emergency contact
    emergency_contact_name = models.CharField(max_length=255, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    
    # Special requirements
    dietary_requirements = models.TextField(blank=True)
    medical_conditions = models.TextField(blank=True)
    accessibility_needs = models.TextField(blank=True)
    
    class Meta:
        ordering = ['booking', 'last_name', 'first_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class ExperienceReview(ProfileMixin):
    """Reviews and ratings for experiences"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    experience = models.ForeignKey(
        Experience,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    booking = models.OneToOneField(
        ExperienceBooking,
        on_delete=models.CASCADE,
        related_name='review'
    )
    
    # Reviewer information (references to users service)
    reviewer_user_id = models.CharField(
        max_length=50,
        help_text="Reference to User ID from users service"
    )
    reviewer_name = models.CharField(max_length=255)
    
    # Review content
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=255, blank=True)
    comment = models.TextField()
    
    # Detailed ratings
    organization_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    instructor_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    venue_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    value_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    
    # Status
    is_verified = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    
    # Response from experience provider
    response = models.TextField(blank=True)
    response_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['experience', 'is_published']),
            models.Index(fields=['reviewer_user_id']),
        ]
    
    def __str__(self):
        return f"Review for {self.experience.title} by {self.reviewer_name}"
