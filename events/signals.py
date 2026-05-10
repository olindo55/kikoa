from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import Participant

@receiver(user_logged_in)
def link_participant_on_login(sender, request, user, **kwargs):
    invitation_token = request.session.get('invitation_token')
    if invitation_token:
        try:
            participant = Participant.objects.get(invitation_token=invitation_token, user__isnull=True)
            participant.user = user
            participant.save()
            request.session['invitation_token_used'] = invitation_token
            del request.session['invitation_token']
        except Participant.DoesNotExist:
            pass

    # Optionnel: Liaison par email si pas de token mais que l'email correspond
    # (Peut être dangereux si les emails ne sont pas vérifiés, mais ici Kikoa semble simple)
    if user.email:
        # On lie tous les participants non liés qui ont cet email
        Participant.objects.filter(email=user.email, user__isnull=True).update(user=user)
