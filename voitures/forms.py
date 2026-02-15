from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Voiture, Avis, Marque  # AJOUTEZ Marque ICI

class InscriptionForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Prénom', 'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Nom', 'class': 'form-control'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Email', 'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Nom d\'utilisateur', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("password1", "password2"):
            field = self.fields.get(name)
            if not field:
                continue
            existing = dict(field.widget.attrs)
            field.widget.attrs = {
                **existing,
                "class": (existing.get("class", "") + " form-control").strip(),
                "placeholder": existing.get("placeholder", "Mot de passe"),
            }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Cet email est déjà utilisé.')
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError('Ce nom d\'utilisateur est déjà pris.')
        return username

class ConnexionForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'Nom d\'utilisateur ou Email',
            'class': 'form-control'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Mot de passe',
            'class': 'form-control'
        })
    )
    remember = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

class VoitureForm(forms.ModelForm):
    class Meta:
        model = Voiture
        fields = [
            'modele', 'prix', 'kilometrage', 'annee', 
            'couleur', 'etat', 'description', 'image_principale'
        ]
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Décrivez votre voiture...'
            }),
            'prix': forms.NumberInput(attrs={'step': '0.01'}),
            'annee': forms.NumberInput(attrs={'min': '1900', 'max': '2026'}),
            'kilometrage': forms.NumberInput(attrs={'min': '0'}),
        }
    
    def clean_prix(self):
        prix = self.cleaned_data.get('prix')
        if prix <= 0:
            raise ValidationError('Le prix doit être supérieur à 0.')
        return prix
    
    def clean_kilometrage(self):
        kilometrage = self.cleaned_data.get('kilometrage')
        if kilometrage < 0:
            raise ValidationError('Le kilométrage ne peut pas être négatif.')
        return kilometrage

class AvisForm(forms.ModelForm):
    class Meta:
        model = Avis
        fields = ['note', 'commentaire']
        widgets = {
            'commentaire': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Donnez votre avis sur cette voiture...',
                'class': 'form-control',
            }),
            'note': forms.Select(choices=[(i, i) for i in range(1, 6)], attrs={'class': 'form-select'})
        }

class RechercheForm(forms.Form):
    marque = forms.ModelChoiceField(
        queryset=Marque.objects.all(),
        required=False,
        empty_label="Toutes les marques",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    prix_min = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Prix minimum'
        })
    )
    prix_max = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Prix maximum'
        })
    )
    annee_min = forms.IntegerField(
        required=False,
        min_value=1900,
        max_value=2026,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Année minimum'
        })
    )
    annee_max = forms.IntegerField(
        required=False,
        min_value=1900,
        max_value=2026,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Année maximum'
        })
    )

class ContactForm(forms.Form):
    nom = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'placeholder': 'Votre nom',
        'class': 'form-control'
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'placeholder': 'Votre email',
        'class': 'form-control'
    }))
    sujet = forms.CharField(max_length=200, widget=forms.TextInput(attrs={
        'placeholder': 'Sujet',
        'class': 'form-control'
    }))
    message = forms.CharField(widget=forms.Textarea(attrs={
        'placeholder': 'Votre message',
        'rows': 5,
        'class': 'form-control'
    }))


class PasswordResetEmailForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Votre email"}
        )


class SetPasswordStyledForm(SetPasswordForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        for name in ("new_password1", "new_password2"):
            self.fields[name].widget.attrs.update({"class": "form-control"})
