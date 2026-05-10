from django.contrib import admin
from .models import Event, Participant, ShoppingItem, Expense


class ParticipantInline(admin.TabularInline):
    model = Participant
    extra = 1


class ShoppingItemInline(admin.TabularInline):
    model = ShoppingItem
    extra = 1


class ExpenseInline(admin.TabularInline):
    model = Expense
    extra = 0
    filter_horizontal = ("split_with",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("emoji", "name", "owner", "date", "created_at")
    list_filter = ("owner",)
    inlines = [ParticipantInline, ShoppingItemInline, ExpenseInline]


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ("name", "event")
    list_filter = ("event",)


@admin.register(ShoppingItem)
class ShoppingItemAdmin(admin.ModelAdmin):
    list_display = ("name", "event", "category", "assignee", "done")
    list_filter = ("event", "category", "done")


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("label", "amount", "payer", "event")
    list_filter = ("event",)
    filter_horizontal = ("split_with",)
