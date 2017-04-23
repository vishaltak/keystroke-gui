from keystrokeapp.custom import pyxhook

import time

class UserLog():

    def __init__(self):
        self.date = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        self.hookman = None
        self.password = ''
        self.pause = False
        self.rawPress = ''
        self.rawRelease = ''
        self.releaseCodes = ''
        self.running = True

    def kbpressevent(self, event):
        if self.pause == False:
            # print key info
            # print(event)
            values = str(event).split()
            self.rawPress += values[1] + ' ' + values[2] + '\n'

    def kbreleaseevent(self, event):
        if self.pause == False:
            # print key info
            # print(event)
            values = str(event).split()
            self.rawRelease += values[1] + ' ' + values[2] + '\n'
            
            # If the ascii value matches enter, terminate the while loop
            if event.Ascii == 13:
                self.running = False
            else:
                if event.VirtualCode != None \
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
        self.pause = False
        # Create hookmanager
        self.hookman = pyxhook.HookManager()
        # Define our callback to fire when a key is pressed down
        self.hookman.KeyDown = self.kbpressevent
        # Define our callback to fire when a key is released
        self.hookman.KeyUp = self.kbreleaseevent
        # Hook the keyboard
        self.hookman.HookKeyboard()
        # Start our listener
        self.hookman.start()
        while self.running:
            time.sleep(0.1)

    def stopLogging(self):
        # Close the listener when we are done
        self.hookman.cancel()

        data = {}
        data['date'] = self.date.replace('T', ' ').strip()
        data['rawPress'] = self.rawPress.strip()
        data['rawRelease'] = self.rawRelease.strip()
        data['releaseCodes'] = self.releaseCodes.strip()
        data['password'] = self.password.strip()
        return data

    def pauseLogging(self):
        self.pause = True