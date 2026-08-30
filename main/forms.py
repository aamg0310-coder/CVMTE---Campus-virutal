from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegistroForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'tu@email.com'}))
    first_name = forms.CharField(required=False, label="Nombre", widget=forms.TextInput(attrs={'placeholder': 'Tu nombre'}))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'usuario'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data.get('first_name', '')
        if commit:
            user.save()
        return user
