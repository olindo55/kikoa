# Intégration dans le projet Kikoa

## 1. Installation

```bash
pip install djangorestframework drf-nested-routers
```

## 2. Copie des fichiers

Copie le dossier `events/` à la racine de ton projet (au même niveau que `manage.py`).

Structure finale :
```
Kikoa/              ← dossier settings.py
events/
  __init__.py
  apps.py
  models.py
  serializers.py
  views.py          ← API DRF
  page_views.py     ← vues HTML
  urls.py           ← router DRF
  admin.py
  migrations/
    __init__.py
  templates/
    events/
      event_list.html
      event_detail.html
manage.py
```

## 3. Kikoa/settings.py

```python
INSTALLED_APPS = [
    # ...apps existantes...
    "rest_framework",
    "events",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}
```

## 4. Kikoa/urls.py — version complète

```python
from django.contrib import admin
from django.urls import path, include
from events import page_views
from events import urls as events_api_urls

urlpatterns = [
    path("admin/", admin.site.urls),

    # Auth Django (login / logout)
    path("accounts/", include("django.contrib.auth.urls")),

    # Events — pages HTML
    path("", page_views.event_list, name="event_list"),
    path("events/<int:pk>/", page_views.event_detail, name="event_detail"),
    path("events/<int:pk>/delete/", page_views.event_delete, name="event_delete"),

    # Events — REST API
    path("api/", include(events_api_urls)),
]
```

> Si tu as déjà d'autres routes dans ton urls.py, ajoute seulement les lignes
> events + api sans toucher au reste.

## 5. Migrations

```bash
python manage.py makemigrations events
python manage.py migrate
```

## 6. Vérification

```bash
python manage.py runserver
```

- `/` → liste des événements (login requis)
- `/events/1/` → app SPA d'un événement
- `/api/events/` → API REST (navigable via DRF)
- `/api/events/1/balance/` → calcul des remboursements

## 7. Endpoints REST disponibles

| Méthode        | URL                                  | Action                   |
|----------------|--------------------------------------|--------------------------|
| GET / POST     | `/api/events/`                       | Liste / Créer            |
| GET/PATCH/DEL  | `/api/events/{id}/`                  | Détail / Modifier / Suppr|
| GET            | `/api/events/{id}/balance/`          | Balance + remboursements |
| GET / POST     | `/api/events/{id}/participants/`     | Liste / Ajouter          |
| PATCH / DEL    | `/api/events/{id}/participants/{n}/` | Modifier / Supprimer     |
| GET / POST     | `/api/events/{id}/items/`            | Liste / Ajouter          |
| PATCH / DEL    | `/api/events/{id}/items/{n}/`        | Modifier / Supprimer     |
| GET / POST     | `/api/events/{id}/expenses/`         | Liste / Ajouter          |
| DEL            | `/api/events/{id}/expenses/{n}/`     | Supprimer                |

## Notes

- Chaque endpoint vérifie que l'événement appartient bien à `request.user`.
- Le CSRF token est injecté par Django dans le template et envoyé par le JS
  dans le header `X-CSRFToken` à chaque requête POST/PATCH/DELETE.
- L'algorithme de balance utilise `Decimal` pour éviter les erreurs d'arrondi
  flottant sur les montants.
