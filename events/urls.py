"""
events/urls.py
--------------
REST API routes (all prefixed with /api/ in the main urls.py):

  GET/POST        /api/events/
  GET/PATCH/DEL   /api/events/{id}/
  GET             /api/events/{id}/balance/

  GET/POST        /api/events/{event_pk}/participants/
  PATCH/DEL       /api/events/{event_pk}/participants/{id}/

  GET/POST        /api/events/{event_pk}/items/
  PATCH/DEL       /api/events/{event_pk}/items/{id}/

  GET/POST        /api/events/{event_pk}/expenses/
  DEL             /api/events/{event_pk}/expenses/{id}/
"""
from rest_framework_nested import routers
from .views import (
    EventViewSet, ParticipantViewSet,
    ShoppingItemViewSet, ExpenseViewSet,
)

router = routers.DefaultRouter()
router.register(r"events", EventViewSet, basename="event")

events_router = routers.NestedDefaultRouter(router, r"events", lookup="event")
events_router.register(r"participants", ParticipantViewSet, basename="event-participant")
events_router.register(r"items", ShoppingItemViewSet, basename="event-item")
events_router.register(r"expenses", ExpenseViewSet, basename="event-expense")

urlpatterns = router.urls + events_router.urls
