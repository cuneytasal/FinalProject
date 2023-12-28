from django import forms
from phonenumber_field.formfields import PhoneNumberField
from django.core.exceptions import ValidationError
import phonenumbers

class LoginForm(forms.Form):
    username = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Email', 'required': True}))
    password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'required': True}))

class RegisterForm(forms.Form):
    cafe_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Cafe Name', 'required': True}))
    name_surname = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Name & Surname', 'required': True}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'E-mail', 'required': True}))
    phone_number = PhoneNumberField(widget=forms.TextInput(attrs={'placeholder': 'Phone Number', 'required': True}))
    password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'placeholder': 'Desired Password', 'required': True}))