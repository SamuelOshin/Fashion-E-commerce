from django import forms
from django.contrib.auth.models import User

class CheckoutForm(forms.Form):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email = forms.EmailField()
    address = forms.CharField(widget=forms.Textarea)
    city = forms.CharField(max_length=50)
    state = forms.CharField(max_length=50)
    zip_code = forms.CharField(max_length=10)
    note = forms.CharField(widget=forms.Textarea)
    payment_method = forms.ChoiceField(choices=[('paypal', 'Paypal'), ('credit_card', 'Credit Card')])
    create_account = forms.BooleanField(required=False)
    password = forms.CharField(widget=forms.PasswordInput, required=False)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email is already in use.")
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if self.cleaned_data.get('create_account') and not password:
            raise forms.ValidationError("Password is required to create an account.")
        return password

class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)