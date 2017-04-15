import bcrypt
import django_rq
import numpy as np
import os
import pandas as pd
import subprocess
import sys

from django import template
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect, render
from sklearn.feature_extraction import FeatureHasher
from sklearn.ensemble import IsolationForest
from sklearn.externals import joblib

from .forms import UsernamePasswordForm
from .models import User
from .custom.userLogging import UserLog

data = None
isLogActive = False
register = template.Library()
sampleSize = 20
userLogInstance = None
windowSize = 100

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
			user = User.objects.create(username=username, password=password, samples=0)
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
		message = None
		if form.is_valid():
			username = form.cleaned_data['username']
			password = form.cleaned_data['password']
			password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
			userExists = User.objects.filter(username=username).exists()
			if userExists == True:
				user = User.objects.get(username=username)
				dbPassword = user.password
				if userId is None:
					userId = user.id
				global data
				if bcrypt.checkpw(data['password'].encode('utf-8'), dbPassword.encode('utf-8')):
					createRecord(genuine=1, userId=userId, username=username)
					addToCSV(userId=userId, sessionId=data['date'], stage='train')
					userSamples = user.samples + 1
					user.samples = userSamples
					user.save()
					if userSamples == sampleSize:
						trainModel(userId)
						return redirect('test',  userId=userId)
					return redirect('train',  userId=userId)
				else:
					message = 'Wrong password'
			else:
				message = 'Wrong Username'

		form = UsernamePasswordForm()
		if userId is not None:
			user = User.objects.get(pk=userId)
			form.initial['username'] = user.username
		stage = 'train'
		context = {'form':form, 'stage':stage, 'message':message}
		return render(request, 'credentials.html', context)
	else:
		# Before rendering the form, stop the logging instance if it exists
		global userLogInstance
		if userLogInstance is not None:
			userLogInstance.stopLogging()
			userLogInstance = None
			global isLogActive
			isLogActive = False
		form = UsernamePasswordForm()
		if userId is not None:
			user = User.objects.get(pk=userId)
			form.initial['username'] = user.username
		stage = 'train'
		context = {'form':form, 'stage':stage}
		return render(request, 'credentials.html', context)

def test(request, userId):
	if request.method == 'POST':
		form = UsernamePasswordForm(request.POST)
		message = None
		if form.is_valid():
			username = form.cleaned_data['username']
			password = form.cleaned_data['password']
			password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
			userExists = User.objects.filter(username=username).exists()
			if userExists == True:
				user = User.objects.get(username=username)
				dbPassword = user.password
				if userId is None:
					userId = user.id
				global data
				if bcrypt.checkpw(data['password'].encode('utf-8'), dbPassword.encode('utf-8')):
					createRecord(genuine=0, userId=userId, username=username)
					addToCSV(userId=userId, sessionId=data['date'], stage='test')
					userSamples = user.samples + 1
					user.samples = userSamples
					user.save()
					result = testModel(userId)
					if result is not None:
						if result == True:
							genuineFile = settings.BASE_DIR + '/keystrokeapp' + settings.STATIC_URL \
								+ 'input/{}/{}/genuine.txt'.format(userId, data['date'])
							with open(genuineFile, 'w') as file:
								file.write(str(1))
							message = 'Welcome!'
						elif result == False:
							message = 'Stay away impostor!'
						# Add the test data to the userData.csv file now that the genuiness has been determined
						addToCSV(userId=userId, sessionId=data['date'], stage='result')
						# Check if the model has to be retrained again
						dataDirectory = settings.BASE_DIR + '/keystrokeapp' + settings.STATIC_URL + 'input/{}/'.format(userId)
						userData = pd.read_csv(dataDirectory + 'userData.csv', header= 0)
						global sampleSize
						if userData.shape[0] % sampleSize == 0:
							trainModel(userId)
						# Return the result
						context = {'message':message, 'userId':userId}
						return render(request, 'result.html', context)
					else:
						message = 'Something went wrong. Please try again.'
				else:
					message = 'Wrong password'
			else:
				message = 'Wrong Username'

		form = UsernamePasswordForm()
		if userId is not None:
			user = User.objects.get(pk=userId)
			form.initial['username'] = user.username
		stage = 'test'
		context = {'form':form, 'stage':stage, 'message':message}
		return render(request, 'credentials.html', context)
	else:
		# Before rendering the form, stop the logging instance if it exists
		global userLogInstance
		if userLogInstance is not None:
			userLogInstance.stopLogging()
			userLogInstance = None
			global isLogActive
			isLogActive = False
		form = UsernamePasswordForm()
		if userId is not None:
			user = User.objects.get(pk=userId)
			form.initial['username'] = user.username
		stage = 'test'
		context = {'form':form, 'stage':stage}
		return render(request, 'credentials.html', context)

def start(request):
	global isLogActive
	if isLogActive == False:
		global userLogInstance
		userLogInstance = UserLog()
		isLogActive = True
		print('Started logging')
		django_rq.enqueue(userLogInstance.startLogging())
	else:
		print('Log is already active')
	return HttpResponse()

def stop(request):
	global isLogActive
	if isLogActive == True:
		global data
		global userLogInstance
		data = userLogInstance.stopLogging()
		userLogInstance = None
		isLogActive = False
		print('Stopped logging')
	return HttpResponse()

def pause(request):
	global isLogActive
	if isLogActive == True:
		global data
		global userLogInstance
		data = userLogInstance.pauseLogging()
		isLogActive = False
		print('Paused logging')
	return HttpResponse()

def createRecord(genuine, userId, username):
	dataDirectory = settings.BASE_DIR + '/keystrokeapp' \
		+ settings.STATIC_URL + 'input/{}/{}/'.format(userId, data['date'])
	if not os.path.exists(dataDirectory):
		os.makedirs(dataDirectory)

	with open(dataDirectory + 'date.txt', 'w') as file:
		file.write(data['date'])

	with open(dataDirectory + 'genuine.txt', 'w') as file:
		file.write(str(genuine))

	with open(dataDirectory + 'login.txt', 'w') as file:
		file.write(username)

	with open(dataDirectory + 'password.txt', 'w') as file:
		file.write(data['password'])

	with open(dataDirectory + 'raw_press.txt', 'w') as file:
		file.write(data['rawPress'])

	with open(dataDirectory + 'raw_release.txt', 'w') as file:
		file.write(data['rawRelease'])

	with open(dataDirectory + 'release_codes.txt', 'w') as file:
		file.write(data['releaseCodes'])

	tempData = None
	with open(dataDirectory + r'raw_press.txt') as f:
		tempData = f.readlines()
	rawPress = []
	for line in tempData:
		temp = line.split()
		rawPress.append(int(temp[1]))

	with open(dataDirectory + r'raw_release.txt') as f:
		tempData = f.readlines()
	rawRelease = []
	for line in tempData:
		temp = line.split()
		rawRelease.append(int(temp[1]))

	pp = []
	pr = []
	rp = []
	rr = []
	for i in range(0, len(rawPress)-1):
		try:
			pp.append(rawPress[i+1] - rawPress[i])
			rp.append(rawPress[i+1] - rawRelease[i])
			rr.append(rawRelease[i+1] - rawRelease[i])
			pr.append(rawRelease[i] - rawPress[i])
		except:
			print('Check extraction.py for i={}'.format(i))
			pass
	pr.append(rawRelease[-1] - rawPress[-1])
	total = rawRelease[-1] - rawPress[0]

	ppFile = open(dataDirectory + 'pp.txt', 'w')
	prFile = open(dataDirectory + 'pr.txt', 'w')
	rpFile = open(dataDirectory + 'rp.txt', 'w')
	rrFile = open(dataDirectory + 'rr.txt', 'w')
	totalFile = open(dataDirectory + 'total.txt', 'w')

	ppFile.write('\n'.join(map(str, pp)))
	prFile.write('\n'.join(map(str, pr)))
	rpFile.write('\n'.join(map(str, rp)))
	rrFile.write('\n'.join(map(str, rr)))
	totalFile.write(str(total))

	ppFile.close()
	prFile.close()
	rpFile.close()
	rrFile.close()
	totalFile.close()

def addToCSV(userId, sessionId, stage):
	dataDirectory = settings.BASE_DIR + '/keystrokeapp' + settings.STATIC_URL + 'input/{}/'.format(userId)
	fileLocation = None
	if stage == 'test':
		fileLocation = dataDirectory + 'tempData.csv'
	else:
		fileLocation = dataDirectory + 'userData.csv'
	csvFile = open(fileLocation, 'a')
	if os.path.getsize(fileLocation) == 0:
		csvFile.write('id,date,genuine,password,release_codes,pp,pr,rp,rr,ppavg,pravg,rpavg,rravg,total\n')
	dataDirectory = dataDirectory + '{}/'.format(sessionId)

	ppavg = 0
	pravg = 0
	rpavg = 0
	rravg = 0

	csvFile.write('\n' + str(userId) + ',')
	with open(dataDirectory + 'date.txt') as f:
		csvFile.write(f.readline() + ',')
	with open(dataDirectory + 'genuine.txt') as f:
		csvFile.write(f.readline() + ',')
	with open(dataDirectory + 'password.txt') as f:
		csvFile.write(f.readline() + ',')
	with open(dataDirectory + 'release_codes.txt') as f:
		csvFile.write(f.readline() + ',')
	with open(dataDirectory + 'pp.txt') as f:
		lines = [line.strip('\n') for line in f.readlines()]
		csvFile.write(' '.join(lines) + ',')
		lines = list(map(int, lines))
		ppavg = sum(lines)/len(lines)
	with open(dataDirectory + 'pr.txt') as f:
		lines = [line.strip('\n') for line in f.readlines()]
		csvFile.write(' '.join(lines) + ',')
		lines = list(map(int, lines))
		pravg = sum(lines)/len(lines)
	with open(dataDirectory + 'rp.txt') as f:
		lines = [line.strip('\n') for line in f.readlines()]
		csvFile.write(' '.join(lines) + ',')
		lines = list(map(int, lines))
		rpavg = sum(lines)/len(lines)
	with open(dataDirectory + 'rr.txt') as f:
		lines = [line.strip('\n') for line in f.readlines()]
		if len(lines) == 0:
			lines.append(str(0))
		csvFile.write(' '.join(lines) + ',')
		lines = list(map(int, lines))
		rravg = sum(lines)/len(lines)
	csvFile.write(str(ppavg) + ',')
	csvFile.write(str(pravg) + ',')
	csvFile.write(str(rpavg) + ',')
	csvFile.write(str(rravg) + ',')
	with open(dataDirectory + 'total.txt') as f:
		csvFile.write(f.readline())
	csvFile.close()

def getHashedMatrix(X):
	X_transformed= []
	temp_list = []
	for i in range(X.shape[0]):
		tempX = X.iloc[i]
		rc = list(tempX.release_codes.split())
		pp = list(map(int, tempX.pp.split()))
		pr = list(map(int, tempX.pr.split()))
		rp = list(map(int, tempX.rp.split()))
		rr = list(map(int, tempX.rr.split()))
		temp_dict = {}
		for j in range(0, len(rc)-1):
			index_str = 'pp.'+ rc[j+1] + '.' + rc[j]
			while temp_dict.get(index_str, -1) != -1:
				index_str = '_' + index_str
			temp_dict[index_str] = pp[j]

			index_str = 'rp.'+ rc[j+1] + '.' + rc[j]
			while temp_dict.get(index_str, -1) != -1:
				index_str = '_' + index_str
			temp_dict[index_str] = rp[j]

			index_str = 'rr.'+ rc[j+1] + '.' + rc[j]
			while temp_dict.get(index_str, -1) != -1:
				index_str = '_' + index_str
			temp_dict[index_str] = rr[j]

			index_str = 'pr.'+ rc[j]
			while temp_dict.get(index_str, -1) != -1:
				index_str = '_' + index_str
			temp_dict[index_str] = pr[j]

		index_str = 'pr.'+ rc[-1]
		while temp_dict.get(index_str, -1) != -1:
			index_str = '_' + index_str
		temp_dict[index_str] = pr[-1]
		temp_dict['ppavg'] = tempX.ppavg
		temp_dict['pravg'] = tempX.pravg
		temp_dict['rpavg'] = tempX.rpavg
		temp_dict['rravg'] = tempX.rravg
		temp_dict['total'] = tempX.total
		temp_list.append(temp_dict)
	hasher= FeatureHasher(n_features=10, input_type='dict', non_negative=True, dtype='int64')
	X_transformed = pd.DataFrame(hasher.fit_transform(temp_list).todense())
	return X_transformed

def trainModel(userId):
	dataDirectory = settings.BASE_DIR + '/keystrokeapp' + settings.STATIC_URL + 'input/{}/'.format(userId)
	userData = pd.read_csv(dataDirectory + 'userData.csv', header= 0)
	global sampleSize
	global windowSize
	if userData.shape[0] % sampleSize == 0:
		# you now have enough samples to create a new/updated model
		if userData.shape[0] > windowSize:
			# move the window i.e use the last 'windowSize' samples
			userData = userData.tail(windowSize)
		X = userData[['release_codes', 'pp','pr', 'rp', 'rr', 'ppavg', 'pravg', 'rpavg', 'rravg', 'total']]
		y = userData['genuine']
		X = getHashedMatrix(X)

		names = [
			'Isolation Forest Ensemble',
		]

		classifiers = [
			IsolationForest(random_state=np.random.RandomState(42)),
		]
		for name, clf in zip(names, classifiers):
			clf.fit(X, y)
			joblib.dump(clf, dataDirectory + 'userModel-{}.pkl'.format(userId, name))
			# print('Dumped model for classifier : {}'.format(name))
		print('Model has been trained')
	else:
		pass

def testModel(userId):
	dataDirectory = settings.BASE_DIR + '/keystrokeapp' + settings.STATIC_URL + 'input/{}/'.format(userId)
	userData = pd.read_csv(dataDirectory + 'tempData.csv', header= 0).tail(1)
	X = userData[['release_codes', 'pp','pr', 'rp', 'rr', 'ppavg', 'pravg', 'rpavg', 'rravg', 'total']]
	X = getHashedMatrix(X)

	names = [
	    "Isolation Forest Ensemble", 
	]

	classifiers = [
		IsolationForest(random_state=np.random.RandomState(42)),
	]
	for name, clf in zip(names, classifiers):
		# print("\nLoading classifier : {}".format(name))
		clf = joblib.load(dataDirectory + 'userModel-{}.pkl'.format(userId, name))
		result = clf.predict(X)
		if result[0] == 1:
			return True
		else:
			return False
	return None