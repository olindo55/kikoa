from rest_framework import serializers
from .models import Event, Participant, ShoppingItem, Expense


class ParticipantSerializer(serializers.ModelSerializer):
    invitation_url = serializers.SerializerMethodField()

    class Meta:
        model = Participant
        fields = ["id", "name", "color", "text_color", "user", "invitation_url"]

    def get_invitation_url(self, obj):
        if obj.user:
            return None
        request = self.context.get("request")
        if request:
            from django.urls import reverse
            return request.build_absolute_uri(
                reverse("accept_invitation", kwargs={"token": obj.invitation_token})
            )
        return None


class ShoppingItemSerializer(serializers.ModelSerializer):
    assignee_detail = ParticipantSerializer(source="assignee", read_only=True)

    class Meta:
        model = ShoppingItem
        fields = [
            "id", "name", "quantity", "category",
            "assignee", "assignee_detail", "done",
        ]


class ExpenseSerializer(serializers.ModelSerializer):
    payer_detail = ParticipantSerializer(source="payer", read_only=True)
    split_with_details = ParticipantSerializer(
        source="split_with", many=True, read_only=True
    )
    # Write: list of participant IDs; Read: handled by split_with_details
    split_with = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Participant.objects.all()
    )

    class Meta:
        model = Expense
        fields = [
            "id", "label", "amount",
            "payer", "payer_detail",
            "split_with", "split_with_details",
            "created_at",
        ]


class EventSerializer(serializers.ModelSerializer):
    participants = ParticipantSerializer(many=True, read_only=True)
    items = ShoppingItemSerializer(many=True, read_only=True)
    expenses = ExpenseSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = [
            "id", "name", "description", "emoji", "date",
            "created_at", "participants", "items", "expenses",
        ]
