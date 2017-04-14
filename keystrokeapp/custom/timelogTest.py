# from django_rq import job
from keystrokeapp.custom import pyxhook

import time

def getLog():
    running = True
    hookman = None

    def kbpressevent(event):
        #print key info
        print(event)

    def kbreleaseevent(event):
        #print key info
        print(event)
        
        #If the ascii value matches enter, terminate the while loop
        if event.Ascii == 13:
            nonlocal running
            running = False

    def startLogging():
        nonlocal hookman
        #Create hookmanager
        hookman = pyxhook.HookManager()
        #Define our callback to fire when a key is pressed down
        hookman.KeyDown = kbpressevent
        #Define our callback to fire when a key is released
        hookman.KeyUp = kbreleaseevent
        #Hook the keyboard
        hookman.HookKeyboard()
        #Start our listener
        hookman.start()
        nonlocal running
        while running:
            time.sleep(0.1)

    def stopLogging():
        nonlocal hookman
        #Close the listener when we are done
        hookman.cancel()

    return startLogging, stopLogging
