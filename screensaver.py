import xbmc
#shell for screensaver actual work takes place in service which monitors screensaverActivated

if __name__ == '__main__':
	while (not xbmc.abortRequested):
		xbmc.sleep(1000)