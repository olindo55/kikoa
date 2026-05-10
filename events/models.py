import uuid
from django.db import models
from django.contrib.auth.models import User


class Event(models.Model):
    """
    A shared event (BBQ, ski weekend, road trip, apéro…).
    Owned by the user who created it.
    """
    name = models.CharField(max_length=200, verbose_name="Nom")
    description = models.TextField(blank=True, verbose_name="Description")
    emoji = models.CharField(max_length=8, default="🎉", verbose_name="Emoji")
    date = models.DateField(null=True, blank=True, verbose_name="Date")
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="events"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Participant(models.Model):
    """
    A named participant in an event.
    Can be linked to a Django user.
    """
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="participants"
    )
    name = models.CharField(max_length=100)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="participations"
    )
    email = models.EmailField(blank=True, null=True)
    invitation_token = models.UUIDField(default=uuid.uuid4, unique=True)
    color = models.CharField(max_length=7, default="#6099e0")
    text_color = models.CharField(max_length=7, default="#ffffff")

    def __str__(self):
        return f"{self.name} ({self.event.name})"


class ShoppingItem(models.Model):
    """An item on the shared shopping/todo list for an event."""

    class Category(models.TextChoices):
        FOOD = "food", "Nourriture"
        DRINK = "drink", "Boisson"
        GEAR = "gear", "Matériel"
        OTHER = "other", "Autre"

    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="items"
    )
    name = models.CharField(max_length=200)
    quantity = models.CharField(max_length=50, blank=True)
    category = models.CharField(
        max_length=10, choices=Category.choices, default=Category.OTHER
    )
    assignee = models.ForeignKey(
        Participant,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="assigned_items",
    )
    done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["done", "created_at"]

    def __str__(self):
        return f"{self.name} — {self.event.name}"


class Expense(models.Model):
    """
    A shared expense: one participant paid, split among several.
    The balance algorithm minimises the number of repayment transactions.
    """
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="expenses"
    )
    label = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    payer = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name="paid_expenses",
    )
    split_with = models.ManyToManyField(
        Participant,
        related_name="shared_expenses",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.label} {self.amount}€ ({self.event.name})"
