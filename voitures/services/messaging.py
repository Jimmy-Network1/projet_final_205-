from __future__ import annotations

from dataclasses import dataclass

from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from voitures.models import Conversation, Message, Voiture


def _ordered_participants(user1: User, user2: User) -> tuple[User, User]:
    if user1.id is None or user2.id is None:
        raise ValueError("Participants must be saved users.")
    return (user1, user2) if user1.id < user2.id else (user2, user1)


def get_or_create_conversation(
    *,
    user1: User,
    user2: User,
    voiture: Voiture | None = None,
    is_support: bool = False,
) -> Conversation:
    a, b = _ordered_participants(user1, user2)
    convo, _ = Conversation.objects.get_or_create(
        participant_a=a,
        participant_b=b,
        voiture=voiture,
        is_support=is_support,
    )
    return convo


@dataclass(frozen=True)
class SendMessageResult:
    conversation: Conversation
    message: Message


def send_message(
    *,
    sender: User,
    recipient: User,
    contenu: str,
    sujet: str,
    voiture: Voiture | None = None,
    is_support: bool = False,
) -> SendMessageResult:
    contenu = (contenu or "").strip()
    sujet = (sujet or "").strip()
    if not contenu:
        raise ValueError("Message vide.")
    if not sujet:
        raise ValueError("Sujet vide.")

    with transaction.atomic():
        convo = get_or_create_conversation(
            user1=sender, user2=recipient, voiture=voiture, is_support=is_support
        )
        msg = Message.objects.create(
            conversation=convo,
            expediteur=sender,
            destinataire=recipient,
            voiture=voiture,
            sujet=sujet[:200],
            contenu=contenu,
        )
        Conversation.objects.filter(id=convo.id).update(updated_at=timezone.now())

    return SendMessageResult(conversation=convo, message=msg)


def user_can_access_conversation(*, convo: Conversation, user: User) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_staff", False):
        return True
    return user.id in {convo.participant_a_id, convo.participant_b_id}


def get_user_conversations_queryset(*, user: User):
    return Conversation.objects.filter(
        Q(participant_a=user) | Q(participant_b=user)
    ).select_related("participant_a", "participant_b", "voiture", "voiture__modele", "voiture__modele__marque")
