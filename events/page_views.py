from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db import models
from .models import Event, Participant
from .forms import UserSignupForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate


@login_required
def event_list(request):
    """Home: list all events owned by the logged-in user or where they participate."""
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        emoji = request.POST.get("emoji", "🎉").strip() or "🎉"
        description = request.POST.get("description", "").strip()
        date = request.POST.get("date") or None
        if name:
            Event.objects.create(
                name=name,
                emoji=emoji,
                description=description,
                date=date,
                owner=request.user,
            )
        return redirect("event_list")

    events = Event.objects.filter(
        models.Q(owner=request.user) | models.Q(participants__user=request.user)
    ).distinct()
    return render(request, "events/event_list.html", {"events": events})


@login_required
def event_detail(request, pk):
    """SPA shell for a single event."""
    event = get_object_or_404(
        Event.objects.filter(
            models.Q(owner=request.user) | models.Q(participants__user=request.user)
        ).distinct(),
        pk=pk
    )
    return render(request, "events/event_detail.html", {"event": event})


@login_required
def event_delete(request, pk):
    """Delete an event (POST only)."""
    event = get_object_or_404(Event, pk=pk, owner=request.user)
    if request.method == "POST":
        event.delete()
    return redirect("event_list")


def signup(request):
    """General signup page."""
    if request.user.is_authenticated:
        return redirect("event_list")
    
    if request.method == "POST":
        form = UserSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            
            # If the user was linked to a participant during login (via signal),
            # redirect them to the event detail instead of the list.
            invitation_token = request.session.get('invitation_token_used')
            if invitation_token:
                try:
                    participant = Participant.objects.get(invitation_token=invitation_token, user=user)
                    del request.session['invitation_token_used']
                    return redirect("event_detail", pk=participant.event.pk)
                except Participant.DoesNotExist:
                    pass

            return redirect("event_list")
    else:
        form = UserSignupForm()
    
    return render(request, "registration/signup.html", {"form": form})


def accept_invitation(request, token):
    """Page to accept an invitation and create a profile or login."""
    participant = get_object_or_404(Participant, invitation_token=token)
    
    # Store token in session for general signup/login
    request.session['invitation_token'] = str(token)
    request.session.modified = True
    
    if participant.user:
        # Invitation already accepted
        if request.user == participant.user:
            return redirect("event_detail", pk=participant.event.pk)
        return redirect(f"{reverse('login')}?next={reverse('event_detail', args=[participant.event.pk])}")

    # If user is already logged in, just associate and redirect
    if request.user.is_authenticated:
        participant.user = request.user
        participant.save()
        return redirect("event_detail", pk=participant.event.pk)

    login_form = AuthenticationForm()
    signup_form = UserSignupForm()

    if request.method == "POST":
        if "action" in request.POST:
            action = request.POST.get("action")
            if action == "signup":
                signup_form = UserSignupForm(request.POST)
                if signup_form.is_valid():
                    user = signup_form.save()
                    participant.user = user
                    participant.save()
                    login(request, user)
                    return redirect("event_detail", pk=participant.event.pk)
            elif action == "login":
                login_form = AuthenticationForm(request, data=request.POST)
                if login_form.is_valid():
                    user = login_form.get_user()
                    participant.user = user
                    participant.save()
                    login(request, user)
                    return redirect("event_detail", pk=participant.event.pk)

    return render(request, "events/accept_invitation.html", {
        "signup_form": signup_form,
        "login_form": login_form,
        "participant": participant,
        "event": participant.event
    })
