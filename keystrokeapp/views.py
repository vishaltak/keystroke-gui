import bcrypt
import subprocess
import sys

from django.http import HttpResponse
from django.shortcuts import redirect, render

from .forms import UsernamePasswordForm
from .models import User
# from django.conf import settings
from .custom.linuxGetTimelog import UserInstance

def index(request):
	return HttpResponse("Welcome to keystroke project!")

def home(request):
	context = {}
	return render(request, 'home.html', context)

def enrol(request):
	if request.method == 'POST':
		form = UsernamePasswordForm(request.POST)
		if form.is_valid():
			username = form.cleaned_data['username']
			password = form.cleaned_data['password']
			password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
			userExists = User.objects.filter(username=username).exists()
			if userExists == True:
				form = UsernamePasswordForm()
				stage = 'enrol'
				message = 'Username already exists.'
				context = {'form':form, 'stage':stage, 'message':message}
				return render(request, 'credentials.html', context)	
			user = User.objects.create(username=username, password=password)
			user.save()
			return redirect('train', user.id)
		else:
			form = UsernamePasswordForm()
			stage = 'enrol'
			context = {'form':form, 'stage':stage}
			return render(request, 'credentials.html', context)
	else:
		form = UsernamePasswordForm()
		stage = 'enrol'
		context = {'form':form, 'stage':stage}
		return render(request, 'credentials.html', context)

def train(request, userId):
	if request.method == 'POST':
		form = UsernamePasswordForm(request.POST)
		if form.is_valid():
			username = form.cleaned_data['username']
			password = form.cleaned_data['password']
			password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
			if userId is None:
				userId = User.objects.get(username=username).id
			return redirect('train',  userId=userId)
		else:
			form = UsernamePasswordForm()
			if userId is not None:
				user = User.objects.get(pk=userId)
				form.initial['username'] = user.username
			stage = 'train'
			context = {'form':form, 'stage':stage}
			return render(request, 'credentials.html', context)
	else:
		form = UsernamePasswordForm()
		if userId is not None:
			user = User.objects.get(pk=userId)
			form.initial['username'] = user.username
			userInstance = UserInstance(userId, user.username, user.password)
			success, date = userInstance.startLogging()
			# userInstance = subprocess.Popen(
			# 	[sys.executable, settings.BASE_DIR + 'keystrokeapp/custom/linuxGetTimeLog.py'], 
			# 	stdout=subprocess.PIPE, 
			# 	stderr=subprocess.STDOUT
			# )
			# print(userInstance.poll())
		stage = 'train'
		context = {'form':form, 'stage':stage}
		return render(request, 'credentials.html', context)

def test(request):
	pass