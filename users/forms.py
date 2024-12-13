from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, required=True, label='Email', help_text='Required. Enter a valid email address.',widget=forms.TextInput(attrs={'class': 'form-control formstyle'}))
    password1 = forms.CharField(max_length=254, required=True, label='Password', widget=forms.PasswordInput(attrs={'class': 'form-control formstyle'}))
    password2 = forms.CharField(max_length=254, required=True, label='Confirm Password', widget=forms.PasswordInput(attrs={'class': 'form-control formstyle'}))
    first_name = forms.CharField(max_length=30, required=True, label='First Name', help_text='Required.',widget=forms.TextInput(attrs={'class': 'form-control formstyle'}))
    last_name = forms.CharField(max_length=30, required=True, label='Last Name', help_text='Required.',widget=forms.TextInput(attrs={'class': 'form-control formstyle'}))
    username = forms.CharField(required=True, label='Username', widget=forms.TextInput(attrs={'class': 'form-control formstyle'}))


    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super(SignUpForm, self).save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

class LoginForm(forms.Form):
    username = forms.CharField(max_length=254)
    password = forms.CharField(widget=forms.PasswordInput)