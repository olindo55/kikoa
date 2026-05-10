from django.contrib import admin
from django.urls import path, include
from events import page_views
from events import urls as events_api_urls

urlpatterns = [
    path("admin/", admin.site.urls),

    # Auth Django (login / logout)
    path("accounts/signup/", page_views.signup, name="signup"),
    path("accounts/", include("django.contrib.auth.urls")),

    # Events — pages HTML
    path("", page_views.event_list, name="event_list"),
    path("events/<int:pk>/", page_views.event_detail, name="event_detail"),
    path("events/<int:pk>/delete/", page_views.event_delete, name="event_delete"),
    path("invitation/<uuid:token>/", page_views.accept_invitation, name="accept_invitation"),

    # Events — REST API
    path("api/", include(events_api_urls)),
]