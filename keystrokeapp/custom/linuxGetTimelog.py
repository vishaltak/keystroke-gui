import bcrypt
import os
import shutil
import time

# import sys
import django
from django.conf import settings

# sys.path.append('/home/tak/Desktop/keystroke')  # path to the parent dir of DjangoTastypie
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keystroke.settings')
# django.setup()

from keystrokeapp.custom import pyxhook

class UserInstance:
    def __init__(self, id, dbUsername, dbPassword):
        self.date = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        self.directory = settings.BASE_DIR + settings.STATIC_URL + 'user_data/{}/{}/'.format(id, self.date)
        print(self.directory)
        
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

        self.count = 0
        self.dbPassword = dbPassword
        self.password = None
        self.running = False
        self.releaseCodes = None
        self.passwordFile = open(self.directory + 'password.txt', 'w')
        self.rawPressFile = open(self.directory + 'raw_press.txt', 'w')
        self.rawReleaseFile = open(self.directory + 'raw_release.txt', 'w')
        self.releaseCodesFile = open(self.directory + 'release_codes.txt', 'w')
        
        userNameFile = open(self.directory + 'login.txt', 'w')
        userNameFile.write(dbUsername)
        userNameFile.close()

        dateFile = open(self.directory + 'date.txt', 'w')
        dateFile.write(self.date.replace('T', ' '))
        dateFile.close()

        genuineFile = open(self.directory + 'genuine.txt', 'w')
        genuineFile.write(str(1))
        genuineFile.close()


    def kbpressevent(self, event):
        print('====Key Press====')
        print(event)
        values = str(event).split()
        self.rawPressFile.write(values[1] + ' ' + values[2] + '\n')

    def kbreleaseevent(self, event):
        print('====Key Release====')
        print(event)
        values = str(event).split()
        self.rawReleaseFile.write(values[1] + ' ' + values[2] + '\n')

        #If the ascii value matches enter, terminate the while loop
        if event.Ascii == 13:
            # if self.count == 1:
            #     self.running = False
            # self.count += 1
            self.running = False
            self.rawReleaseFile = open(self.directory + 'raw_release.txt', 'w')
        else:
            if event.VirtualCode != None\
                and (event.VirtualCode == 16 \
                or event.VirtualCode == 32 \
                or (event.VirtualCode >= 48 and event.VirtualCode <= 57) \
                or (event.VirtualCode >= 65 and event.VirtualCode <= 90) \
                or (event.VirtualCode >= 96 and event.VirtualCode <= 105) \
                or (event.VirtualCode >= 186 and event.VirtualCode <= 192) \
                or (event.VirtualCode >= 219 and event.VirtualCode <= 222)
                ):
                self.password += values[0]
            self.releaseCodes += ' ' + values[1]

    def startLogging(self):

        self.password = ''
        self.releaseCodes = ''
        #Create hookmanager
        hookman = pyxhook.HookManager()
        #Define our callback to fire when a key is pressed down
        hookman.KeyDown = self.kbpressevent
        #Define our callback to fire when a key is released
        hookman.KeyUp = self.kbreleaseevent
        #Hook the keyboard
        hookman.HookKeyboard()
        #Start our listener
        hookman.start()

        #Create a loop to keep the application running
        self.running = True
        while self.running:
            time.sleep(0.1)

        #Close the listener when we are done
        hookman.cancel()

        self.passwordFile.write(self.password)
        self.releaseCodesFile.write(self.releaseCodes.strip())

        #Closed the files
        self.passwordFile.close()
        self.rawPressFile.close()
        self.rawReleaseFile.close()
        self.releaseCodesFile.close()

        print('Password==>'.format(self.password))

        if not bcrypt.checkpw(self.password.encode('utf-8'), self.dbPassword.encode('utf-8')):
            # shutil.rmtree(self.directory)
            print("please Remove the sample as password did not match")
            return False, None
        else:
            print("Sample accepted")
            return True, self.date