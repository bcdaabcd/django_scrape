from django import forms
from django.contrib import auth
from django.contrib.auth.models import User

class SignInForm(forms.Form):
    name = forms.CharField(widget=forms.TextInput())
    password = forms.CharField(widget=forms.PasswordInput())

    def clean(self):
        username = self.cleaned_data['name']
        password = self.cleaned_data['password']
        user = auth.authenticate(username=username,password=password)
        if user is None:
            raise forms.ValidationError('incorrect username or password')
        else:
            self.cleaned_data['user'] = user
        return self.cleaned_data
    

class SignUpForm(forms.Form):
    name = forms.CharField(widget=forms.TextInput(),max_length=30,min_length=2)
    email = forms.EmailField(widget=forms.EmailInput())
    password = forms.CharField(widget=forms.PasswordInput())
    password_again = forms.CharField(widget=forms.PasswordInput())
    def clean_username(self):
        username = self.cleaned_data['name']
        if User.objects.filter(username=username):
            raise forms.ValidationError('Username already exists')
        return username
    def clean_email(self):
        email = self.cleaned_data['name']
        if User.objects.filter(email=email):
            raise forms.ValidationError('Email already exists')
        return email
    def clean_password_again(self):
        password = self.cleaned_data['password']
        password_again = self.cleaned_data['password_again']
        if password_again != password:
            raise forms.ValidationError('Two passwords do not match')
        else:
            return password
