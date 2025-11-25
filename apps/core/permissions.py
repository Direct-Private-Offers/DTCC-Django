from rest_framework.permissions import BasePermission


class IsInGroup(BasePermission):
    """
    Permission that checks if the authenticated user is in a required Django Group.

    Usage:
      class MyView(APIView):
          permission_classes = [IsAuthenticated & IsInGroup.with_names(["issuer"]) ]
    """

    required_groups = []

    def __init__(self, required_groups=None):
        if required_groups is not None:
            self.required_groups = required_groups

    @classmethod
    def with_names(cls, names):
        return cls(required_groups=list(names))

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        if not self.required_groups:
            return True
        user_groups = set(user.groups.values_list('name', flat=True))
        return any(g in user_groups for g in self.required_groups)
