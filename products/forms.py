from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

class CheckoutForm(forms.Form):
    first_name = forms.CharField(max_length=50, label='First Name')
    last_name = forms.CharField(max_length=50, label='Last Name')
    email = forms.EmailField(label='Email')
    address = forms.CharField(widget=forms.Textarea, label='Address')
    city = forms.CharField(max_length=50, label='City')
    state = forms.CharField(max_length=50, label='State')
    zip_code = forms.CharField(max_length=10, label='Zip Code')
    note = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Notes about your order, e.g. special notes for delivery.'}),
        required=False,
        label='Note'
    )
    payment_method = forms.ChoiceField(
        choices=[('pay_on_delivery', 'Pay on Delivery'), ('paystack', 'Pay Now (Paystack)')],
        label='Payment Method'
    )
    create_account = forms.BooleanField(required=False, label='Create an account?')
    password1 = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label='Password',
        help_text='Enter a password if you want to create an account.'
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label='Confirm Password',
        help_text='Enter the same password as before, for verification.'
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            if self.user and self.user.is_authenticated and self.user.email == email:
                return email
            raise forms.ValidationError("Email is already in use.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        create_account = cleaned_data.get('create_account')
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if create_account:
            if not password1 or not password2:
                raise forms.ValidationError("Both password fields are required to create an account.")
            if password1 != password2:
                raise forms.ValidationError("Passwords do not match.")
            try:
                validate_password(password1)
            except forms.ValidationError as e:
                self.add_error('password1', e)
        return cleaned_data

class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)