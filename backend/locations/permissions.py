from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Дозволяє читати будь-кому, але редагувати/видаляти тільки власнику обʼєкта.
    Використовується в LocationViewSet.
    """

    def has_object_permission(self, request, view, obj):
        # GET, HEAD, OPTIONS — дозволено всім
        if request.method in permissions.SAFE_METHODS:
            return True
        # Запис — тільки власник
        return obj.owner == request.user