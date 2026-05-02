from rest_framework import serializers
from .models import Collection, CollectionMember
from locations.serializers import LocationSerializer


class CollectionMemberSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = CollectionMember
        fields = ('id', 'user', 'user_email', 'username', 'role', 'joined_at')
        read_only_fields = ('joined_at',)


class CollectionSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)
    locations_count = serializers.IntegerField(read_only=True)
    members_count = serializers.IntegerField(read_only=True)
    # Показуємо чи поточний юзер є членом (заповнюється у view)
    user_role = serializers.SerializerMethodField()

    class Meta:
        model = Collection
        fields = (
            'id', 'name', 'description', 'cover_image',
            'owner', 'is_public',
            'locations_count', 'members_count', 'user_role',
            'created_at', 'updated_at',
        )
        read_only_fields = ('owner', 'invite_token', 'created_at', 'updated_at')

    def get_user_role(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        if obj.owner == request.user:
            return 'owner'
        member = obj.members.filter(user=request.user).first()
        return member.role if member else None


class CollectionDetailSerializer(CollectionSerializer):
    """Детальний серіалайзер — включає список локацій і учасників."""
    locations = LocationSerializer(many=True, read_only=True)
    members = CollectionMemberSerializer(many=True, read_only=True)

    class Meta(CollectionSerializer.Meta):
        fields = CollectionSerializer.Meta.fields + ('locations', 'members', 'invite_token')


class AddLocationSerializer(serializers.Serializer):
    """Для додавання/видалення локацій з колекції."""
    location_id = serializers.IntegerField()


class InviteSerializer(serializers.Serializer):
    """Для прийняття запрошення за токеном."""
    token = serializers.UUIDField()


class SetMemberRoleSerializer(serializers.Serializer):
    """Для зміни ролі учасника."""
    user_id = serializers.IntegerField()
    role = serializers.ChoiceField(choices=CollectionMember.ROLE_CHOICES)
