from rest_framework import permissions
from rest_framework.permissions import BasePermission


class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.owner == request.user


class IsProfileMember(BasePermission):
    """
    Custom permission to check if user belongs to the same profile
    as the object being accessed.
    """

    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return False
        
        # Check if user has an active profile
        return hasattr(request.user, 'profile') and request.user.profile is not None

    def has_object_permission(self, request, view, obj):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile') or request.user.profile is None:
            return False

        # For objects that have a direct profile relationship
        if hasattr(obj, 'profile'):
            return obj.profile == request.user.profile

        # For objects that have profile through owner
        if hasattr(obj, 'owner') and hasattr(obj.owner, 'profile'):
            return obj.owner.profile == request.user.profile

        # For Experience objects (profile through owner)
        if hasattr(obj, 'owner'):
            return obj.owner == request.user

        # For ExperienceBooking objects (profile through customer)
        if hasattr(obj, 'customer') and hasattr(obj.customer, 'profile'):
            return obj.customer.profile == request.user.profile

        # For ExperienceSession objects (profile through experience owner)
        if hasattr(obj, 'experience') and hasattr(obj.experience, 'owner'):
            return obj.experience.owner == request.user

        # For ExperienceReview objects (profile through customer or experience owner)
        if hasattr(obj, 'customer') and hasattr(obj.customer, 'profile'):
            # Customer can access their own reviews
            if obj.customer.profile == request.user.profile:
                return True
        
        if hasattr(obj, 'experience') and hasattr(obj.experience, 'owner'):
            # Experience owner can access reviews for their experiences
            return obj.experience.owner == request.user

        return False


class IsExperienceOwner(BasePermission):
    """
    Custom permission for experience owners to manage their experiences.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # For Experience objects
        if hasattr(obj, 'owner'):
            return obj.owner == request.user

        # For ExperienceSession objects
        if hasattr(obj, 'experience'):
            return obj.experience.owner == request.user

        # For ExperienceBooking objects (experience owner can manage bookings)
        if hasattr(obj, 'session') and hasattr(obj.session, 'experience'):
            return obj.session.experience.owner == request.user

        return False


class IsCustomerOrExperienceOwner(BasePermission):
    """
    Permission for both customers and experience owners to access booking data.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Customer can access their own bookings
        if hasattr(obj, 'customer'):
            if obj.customer == request.user:
                return True

        # Experience owner can access bookings for their experiences
        if hasattr(obj, 'session') and hasattr(obj.session, 'experience'):
            if obj.session.experience.owner == request.user:
                return True

        return False


class IsReviewOwnerOrExperienceOwner(BasePermission):
    """
    Permission for review owners and experience owners to manage reviews.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Review owner can manage their own reviews
        if hasattr(obj, 'customer'):
            if obj.customer == request.user:
                return True

        # Experience owner can view (but not edit) reviews for their experiences
        if hasattr(obj, 'experience'):
            if obj.experience.owner == request.user:
                # Experience owners can only read reviews, not modify them
                if request.method in permissions.SAFE_METHODS:
                    return True

        return False


class CanCreateExperience(BasePermission):
    """
    Permission to check if user can create experiences.
    This could be extended to check for specific roles or subscriptions.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile') or request.user.profile is None:
            return False

        # Add additional checks here if needed (e.g., subscription level, verification status)
        # For now, any authenticated user with a profile can create experiences
        return True


class CanBookExperience(BasePermission):
    """
    Permission to check if user can book experiences.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Check if user has a profile
        if not hasattr(request.user, 'profile') or request.user.profile is None:
            return False

        return True

    def has_object_permission(self, request, view, obj):
        # Users cannot book their own experiences
        if hasattr(obj, 'experience') and hasattr(obj.experience, 'owner'):
            if obj.experience.owner == request.user:
                return False

        # Check if session is available and has capacity
        if hasattr(obj, 'session'):
            if not obj.session.is_available or obj.session.available_spots <= 0:
                return False

        return True
