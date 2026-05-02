from rest_framework import permissions
from .models import CollectionMember


class IsCollectionOwner(permissions.BasePermission):
    """Тільки власник колекції може її редагувати або видаляти."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user


class IsCollectionOwnerOrEditor(permissions.BasePermission):
    """
    Власник або редактор може додавати/видаляти локації.
    Переглядач і анонім — тільки читати (якщо колекція публічна).
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            # Публічну колекцію читає будь-хто, приватну — тільки власник і члени
            if obj.is_public:
                return True
            if not request.user.is_authenticated:
                return False
            return (
                obj.owner == request.user
                or obj.members.filter(user=request.user).exists()
            )

        # Запис — власник або редактор
        if not request.user.is_authenticated:
            return False
        if obj.owner == request.user:
            return True
        return obj.members.filter(
            user=request.user, role=CollectionMember.ROLE_EDITOR
        ).exists()
