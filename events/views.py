from django.db import models
from decimal import Decimal
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Event, Participant, ShoppingItem, Expense
from .serializers import (
    EventSerializer, ParticipantSerializer,
    ShoppingItemSerializer, ExpenseSerializer,
)


# ── Permission helper ─────────────────────────────────────────────────────────

class IsEventOwnerOrParticipant(permissions.BasePermission):
    """Owner can do everything, participants can view and interact."""

    def has_object_permission(self, request, view, obj):
        event = obj if isinstance(obj, Event) else obj.event
        if event.owner == request.user:
            return True
        
        # Check if user is a participant
        return event.participants.filter(user=request.user).exists()


# ── Event ─────────────────────────────────────────────────────────────────────

class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated, IsEventOwnerOrParticipant]

    def get_queryset(self):
        # Events owned by user OR where user is a participant
        return (
            Event.objects
            .filter(models.Q(owner=self.request.user) | models.Q(participants__user=self.request.user))
            .distinct()
            .prefetch_related(
                "participants",
                "items__assignee",
                "expenses__payer",
                "expenses__split_with",
            )
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["get"])
    def balance(self, request, pk=None):
        """
        Compute each participant's net balance and the minimal
        list of repayment transactions (greedy debt simplification).
        """
        event = self.get_object()
        balances = {p.id: Decimal("0") for p in event.participants.all()}

        for expense in event.expenses.prefetch_related("split_with").all():
            if expense.payer_id not in balances:
                continue
            split_count = expense.split_with.count()
            if split_count == 0:
                continue
            share = expense.amount / split_count
            balances[expense.payer_id] += expense.amount
            for p in expense.split_with.all():
                if p.id in balances:
                    balances[p.id] -= share

        participant_map = {p.id: p for p in event.participants.all()}
        balance_list = [
            {
                "id": pid,
                "name": participant_map[pid].name,
                "color": participant_map[pid].color,
                "net": float(round(net, 2)),
            }
            for pid, net in balances.items()
        ]
        settlements = _compute_settlements(balances, participant_map)
        return Response({"balances": balance_list, "settlements": settlements})


def _compute_settlements(balances, participant_map):
    """Greedy algorithm: minimise number of transactions to settle all debts."""
    EPSILON = Decimal("0.005")
    debtors = []
    creditors = []

    for pid, net in balances.items():
        if net < -EPSILON:
            debtors.append({"id": pid, "amount": -net})
        elif net > EPSILON:
            creditors.append({"id": pid, "amount": net})

    debtors.sort(key=lambda x: x["amount"], reverse=True)
    creditors.sort(key=lambda x: x["amount"], reverse=True)

    settlements = []
    i = j = 0
    while i < len(debtors) and j < len(creditors):
        d, c = debtors[i], creditors[j]
        transfer = min(d["amount"], c["amount"])
        settlements.append({
            "from_id": d["id"],
            "from_name": participant_map[d["id"]].name,
            "from_color": participant_map[d["id"]].color,
            "to_id": c["id"],
            "to_name": participant_map[c["id"]].name,
            "to_color": participant_map[c["id"]].color,
            "amount": float(round(transfer, 2)),
        })
        d["amount"] -= transfer
        c["amount"] -= transfer
        if d["amount"] < EPSILON:
            i += 1
        if c["amount"] < EPSILON:
            j += 1

    return settlements


# ── Participants ──────────────────────────────────────────────────────────────

class ParticipantViewSet(viewsets.ModelViewSet):
    serializer_class = ParticipantSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Participant.objects.filter(
            models.Q(event__owner=self.request.user) | models.Q(event__participants__user=self.request.user),
            event_id=self.kwargs["event_pk"],
        ).distinct()

    def perform_create(self, serializer):
        from django.shortcuts import get_object_or_404
        event = get_object_or_404(
            Event.objects.filter(
                models.Q(owner=self.request.user) | models.Q(participants__user=self.request.user)
            ),
            pk=self.kwargs["event_pk"]
        )
        serializer.save(event=event)


# ── Shopping items ────────────────────────────────────────────────────────────

class ShoppingItemViewSet(viewsets.ModelViewSet):
    serializer_class = ShoppingItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ShoppingItem.objects.filter(
            models.Q(event__owner=self.request.user) | models.Q(event__participants__user=self.request.user),
            event_id=self.kwargs["event_pk"],
        ).select_related("assignee").distinct()

    def perform_create(self, serializer):
        from django.shortcuts import get_object_or_404
        event = get_object_or_404(
            Event.objects.filter(
                models.Q(owner=self.request.user) | models.Q(participants__user=self.request.user)
            ),
            pk=self.kwargs["event_pk"]
        )
        serializer.save(event=event)


# ── Expenses ──────────────────────────────────────────────────────────────────

class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Expense.objects.filter(
            models.Q(event__owner=self.request.user) | models.Q(event__participants__user=self.request.user),
            event_id=self.kwargs["event_pk"],
        ).select_related("payer").prefetch_related("split_with").distinct()

    def perform_create(self, serializer):
        from django.shortcuts import get_object_or_404
        event = get_object_or_404(
            Event.objects.filter(
                models.Q(owner=self.request.user) | models.Q(participants__user=self.request.user)
            ),
            pk=self.kwargs["event_pk"]
        )
        serializer.save(event=event)
