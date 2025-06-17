from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and register viewsets
router = DefaultRouter()
router.register(r'categories', views.ExperienceCategoryViewSet, basename='experiencecategory')
router.register(r'experiences', views.ExperienceViewSet, basename='experience')
router.register(r'bookings', views.ExperienceBookingViewSet, basename='experiencebooking')
router.register(r'reviews', views.ExperienceReviewViewSet, basename='experiencereview')
router.register(r'sessions', views.ExperienceSessionViewSet, basename='experiencesession')

# Custom URL patterns for specific endpoints
urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Experience-specific endpoints
    path('experiences/<int:experience_id>/sessions/', 
         views.ExperienceSessionViewSet.as_view({'get': 'list', 'post': 'create'}), 
         name='experience-sessions'),
    
    path('experiences/<int:experience_id>/reviews/', 
         views.ExperienceReviewViewSet.as_view({'get': 'list', 'post': 'create'}), 
         name='experience-reviews'),
    
    path('experiences/<int:experience_id>/book/', 
         views.ExperienceViewSet.as_view({'post': 'book'}), 
         name='experience-book'),
    
    path('experiences/<int:experience_id>/availability/', 
         views.ExperienceViewSet.as_view({'get': 'availability'}), 
         name='experience-availability'),
    
    # Category-specific endpoints
    path('categories/<int:category_id>/experiences/', 
         views.ExperienceViewSet.as_view({'get': 'list'}), 
         name='category-experiences'),
    
    # Booking management endpoints
    path('bookings/<int:booking_id>/confirm/', 
         views.ExperienceBookingViewSet.as_view({'post': 'confirm'}), 
         name='booking-confirm'),
    
    path('bookings/<int:booking_id>/cancel/', 
         views.ExperienceBookingViewSet.as_view({'post': 'cancel'}), 
         name='booking-cancel'),
    
    path('bookings/<int:booking_id>/complete/', 
         views.ExperienceBookingViewSet.as_view({'post': 'complete'}), 
         name='booking-complete'),
    
    # Review management endpoints
    path('reviews/<int:review_id>/respond/', 
         views.ExperienceReviewViewSet.as_view({'post': 'respond'}), 
         name='review-respond'),
    
    # Session management endpoints
    path('sessions/<int:session_id>/book/', 
         views.ExperienceSessionViewSet.as_view({'post': 'book'}), 
         name='session-book'),
    
    path('sessions/<int:session_id>/cancel/', 
         views.ExperienceSessionViewSet.as_view({'post': 'cancel'}), 
         name='session-cancel'),
    
    # Search and filter endpoints
    path('search/', 
         views.ExperienceViewSet.as_view({'get': 'search'}), 
         name='experience-search'),
    
    path('featured/', 
         views.ExperienceViewSet.as_view({'get': 'featured'}), 
         name='experience-featured'),
    
    path('popular/', 
         views.ExperienceViewSet.as_view({'get': 'popular'}), 
         name='experience-popular'),
    
    # Statistics and analytics endpoints
    path('stats/', 
         views.ExperienceViewSet.as_view({'get': 'stats'}), 
         name='experience-stats'),
    
    path('categories/stats/', 
         views.ExperienceCategoryViewSet.as_view({'get': 'stats'}), 
         name='category-stats'),
]

app_name = 'experiences'
