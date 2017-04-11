from django import forms

class UsernamePasswordForm(forms.Form):
	username = forms.CharField(label='Username', max_length=50)
	password = forms.CharField(label='Password', max_length=50, widget=forms.PasswordInput())