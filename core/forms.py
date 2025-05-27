from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model

class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="E-MAIL",
        widget=forms.EmailInput(attrs={
            'autofocus': True,
            'class': 'form-control',
            'placeholder': 'usuario@ejemplo.com'
        })
    )

    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email__iexact=email)
            self.cleaned_data['username'] = user.username
        except UserModel.DoesNotExist:
            pass  # El AuthenticationForm se encargará del error
        return super().clean()
