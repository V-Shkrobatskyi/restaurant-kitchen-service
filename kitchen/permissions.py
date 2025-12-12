from django.contrib.auth.mixins import UserPassesTestMixin


class BaseRolePermission(UserPassesTestMixin):
    """Base class for role-based permission checks."""

    def test_func(self):
        # Block if the user is not authenticated
        if not self.request.user.is_authenticated:
            return False
        return self.has_permission()

    def has_permission(self):
        """Override this method in subclasses."""
        return False


class IsCookOrStaff(BaseRolePermission):
    """Access: Cooks, Staff, Admin."""

    def has_permission(self):
        user = self.request.user
        return user.is_staff or user.role in ['staff', 'cook']


class IsStaffOrAdmin(BaseRolePermission):
    """Access: Staff and Admin only."""

    def has_permission(self):
        user = self.request.user
        return user.is_staff or user.role == 'staff'


class IsAdminUser(BaseRolePermission):
    """Access: Admin only (is_staff=True)."""

    def has_permission(self):
        return self.request.user.is_staff
