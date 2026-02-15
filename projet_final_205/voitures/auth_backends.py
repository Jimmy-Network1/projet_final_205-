from __future__ import annotations

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q


class UsernameOrEmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        identifier = str(username).strip()
        if not identifier:
            return None

        try:
            user = User.objects.get(Q(username__iexact=identifier) | Q(email__iexact=identifier))
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            # Shouldn't happen if emails are unique, but fall back to username match.
            try:
                user = User.objects.get(username__iexact=identifier)
            except User.DoesNotExist:
                return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

