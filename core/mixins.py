from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied

class StudentRequiredMixin(UserPassesTestMixin):
    """Verify that the current user is a student."""
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        return self.request.user.role == User.Role.STUDENT
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        raise PermissionDenied("This page is only available to students.")

class MentorRequiredMixin(UserPassesTestMixin):
    """Verify that the current user is a mentor."""
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        return hasattr(self.request.user, 'mentor_profile')
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        raise PermissionDenied("This page is only available to mentors.")
