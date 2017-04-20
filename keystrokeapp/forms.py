from django import forms

class UsernamePasswordForm(forms.Form):
	username = forms.CharField(label='Username', max_length=50, widget=forms.TextInput(attrs={'id':'username', 'class':'form-control', 'placeholder':'Username'}))
	password = forms.CharField(label='Password', max_length=50, widget=forms.PasswordInput(attrs={'id':'password', 'class':'form-control', 'placeholder':'Password'}))