# Random trailer player
#
# Author - kzeleny
# Version - 1.1.6
# Compatibility - Frodo/Gothum
#

import xbmc
import xbmcvfs
import xbmcgui
from urllib import quote_plus, unquote_plus
import datetime
import urllib
import urllib2
import re
import sys
import os
import random
import json
import time
import xbmcaddon

addon = xbmcaddon.Addon()
number_trailers =  addon.getSetting('number_trailers')
do_curtains = 'false'
do_genre = addon.getSetting('do_genre')
do_volume = addon.getSetting('do_volume')
volume = int(addon.getSetting("volume"))
path = addon.getSetting('path')
do_library=addon.getSetting('do_library')
do_folder=addon.getSetting('do_folder')
do_itunes=addon.getSetting('do_itunes')
do_multiple = False
if do_library=='true' and (do_folder=='true' or do_itunes=='true'):do_multiple = True
if do_folder=='true' and (do_library=='true' or do_itunes=='true'):do_multiple = True
if do_itunes=='true' and (do_folder=='true') or do_library=='true':do_multiple = True
if volume > 100:
    do_volume='false'
currentVolume = xbmc.getInfoLabel("Player.Volume")
currentVolume = int((float(currentVolume.split(" ")[0])+60.0)/60.0*100.0)
trailer_type = int(addon.getSetting('trailer_type'))
g_action = addon.getSetting('g_action') == 'true'
g_comedy = addon.getSetting('g_comedy') == 'true'
g_docu = addon.getSetting('g_docu') == 'true'
g_drama = addon.getSetting('g_drama') == 'true'
g_family = addon.getSetting('g_family') == 'true'
g_fantasy = addon.getSetting('g_fantasy') == 'true'
g_foreign = addon.getSetting('g_foreign') == 'true'
g_horror = addon.getSetting('g_horror') == 'true'
g_musical = addon.getSetting('g_musical') == 'true'
g_romance = addon.getSetting('g_romance') == 'true'
g_scifi = addon.getSetting('g_scifi') == 'true'
g_thriller = addon.getSetting('g_thriller') == 'true'
hide_info = addon.getSetting('hide_info')
hide_title = addon.getSetting('hide_title')
trailers_path = addon.getSetting('path')
addon_path = addon.getAddonInfo('path')
hide_watched = addon.getSetting('hide_watched')
watched_days = addon.getSetting('watched_days')
resources_path = xbmc.translatePath( os.path.join( addon_path, 'resources' ) ).decode('utf-8')
media_path = xbmc.translatePath( os.path.join( resources_path, 'media' ) ).decode('utf-8')
open_curtain_path = xbmc.translatePath( os.path.join( media_path, 'OpenSequence.mp4' ) ).decode('utf-8')
close_curtain_path = xbmc.translatePath( os.path.join( media_path, 'ClosingSequence.mp4' ) ).decode('utf-8')
selectedGenre =''
exit_requested = False
movie_file = ''
addonID = "screensaver.randomtrailers"
addonUserDataFolder = xbmc.translatePath("special://profile/addon_data/"+addonID)
cacheFile = xbmc.translatePath("special://profile/addon_data/"+addonID+"/cache")
cacheLifetime = 24
if not os.path.isdir(addonUserDataFolder):
  os.mkdir(addonUserDataFolder)
opener = urllib2.build_opener()
opener.addheaders = [('User-Agent', 'iTunes')]
urlMain = "http://trailers.apple.com"

if len(sys.argv) == 2:
    do_genre ='false'

trailer=''
do_timeout = False
played = []

def askGenres():
    addon = xbmcaddon.Addon()
    # default is to select from all movies
    selectGenre = False
    # ask user whether they want to select a genre
    a = xbmcgui.Dialog().yesno(addon.getLocalizedString(32100), addon.getLocalizedString(32101))
    # deal with the output
    if a == 1: 
    # set filter
        selectGenre = True
    return selectGenre  
  
def selectGenre():
  success = False
  selectedGenre = ""
  myGenres = []
  trailerstring = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "properties": ["genre", "playcount", "file", "trailer"]}, "id": 1}')
  trailerstring = unicode(trailerstring, 'utf-8', errors='ignore')
  trailers = json.loads(trailerstring)
  for movie in trailers["result"]["movies"]:
    # Let's get the movie genres
    genres = movie["genre"]
    for genre in genres:
        # check if the genre is a duplicate
        if not genre in myGenres:
          # if not, add it to our list
          myGenres.append(genre)
  # sort the list alphabeticallt        
  mySortedGenres = sorted(myGenres)
  # prompt user to select genre
  selectGenre = xbmcgui.Dialog().select(addon.getLocalizedString(32100), mySortedGenres)
  # check whether user cancelled selection
  if not selectGenre == -1:
    # get the user's chosen genre
    selectedGenre = mySortedGenres[selectGenre]
    success = True
  else:
    success = False
  # return the genre and whether the choice was successfult
  return success, selectedGenre

def checkRating(rating):
    passed = False
    rating_limit = addon.getSetting('rating_limit')
    do_notyetrated = addon.getSetting('do_notyetrated')
    do_nr = addon.getSetting('do_nr')
    nyr=''
    nr=''
    if do_notyetrated=='true':nyr='Not yet rated'
    if do_nr == 'true':nr='NR'
    if rating_limit=='0':passed=True
    if rating_limit=='1':
        rating_limit=['G',nr,nyr]
    if rating_limit=='2':
        rating_limit=['G','PG',nr,nyr]
    if rating_limit=='3':
        rating_limit=['G','PG','PG-13',nr,nyr]
    if rating_limit=='4':
        rating_limit=['G','PG','PG-13','R',nr,nyr]
    if rating_limit=='5':
        rating_limit=['G','PG','PG-13','R','NC-17',nr,nyr]
    if rating in rating_limit:passed=True
    return passed
    
def genreCheck(genres):
    passed = True
    if not g_action:
        if "Action and Adventure" in genres:
            passed = False
    if not g_comedy:
        if "Comedy" in genres:
            passed = False
    if not g_docu:
        if "Documentary" in genres:
            passed = False
    if not g_drama:
        if "Drama" in genres:
            passed = False
    if not g_family:
        if "Family" in genres:
            passed = False
    if not g_fantasy:
        if "Fantasy" in genres:
            passed = False
    if not g_foreign:
        if "Foreign" in genres:
            passed = False
    if not g_horror:
        if "Horror" in genres:
            passed = False
    if not g_musical:
        if "Musical" in genres:
            passed = False
    if not g_romance:
        if "Romance" in genres:
            passed = False
    if not g_scifi:
        if "Science Fiction" in genres:
            passed = False
    if not g_thriller:
        if "Thriller" in genres:
            passed = False
    return passed
    
def getVideos():
    trailers=[]
    do_clips=addon.getSetting('do_clips')
    do_featurettes=addon.getSetting('do_featurettes')
    if trailer_type == 0:content = opener.open(urlMain+"/trailers/home/feeds/studios.json").read()
    if trailer_type == 1:content = opener.open(urlMain+"/trailers/home/feeds/just_added.json").read()
    if trailer_type == 2:content = opener.open(urlMain+"/trailers/home/feeds/most_pop.json").read()
    if trailer_type == 3:content = opener.open(urlMain+"/trailers/home/feeds/exclusive.json").read()
    if trailer_type == 4:content = opener.open(urlMain+"/trailers/home/feeds/studios.json").read()
    content = content.decode('unicode_escape').encode('ascii','ignore')
    spl = content.split('"title"')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('"poster":"(.+?)"', re.DOTALL).findall(entry)
        thumb = urlMain+match[0].replace('poster.jpg', 'poster-xlarge.jpg')
        match = re.compile('"rating":"(.+?)"', re.DOTALL).findall(entry)
        rating = match[0]
        fanart = urlMain+match[0].replace('poster.jpg', 'background.jpg')
        match = re.compile('"releasedate":"(.+?)"', re.DOTALL).findall(entry)
        if len(match)>0:
            month = match[0][8:-20]
            day = int(match[0][5:-24])
            year = int(match[0][12:-15])
            if month=='Jan':month=1
            if month=='Feb':month=2
            if month=='Mar':month=3
            if month=='Apr':month=4
            if month=='May':month=5
            if month=='Jun':month=6
            if month=='Jul':month=7
            if month=='Aug':month=8
            if month=='Sep':month=9
            if month=='Oct':month=10
            if month=='Nov':month=11
            if month=='Dec':month=12
            releasedate = datetime.date(year,month,day)
        else:
            releasedate = datetime.date.today()
        match = re.compile('"(.+?)"', re.DOTALL).findall(entry)
        title = match[0]
        match = re.compile('"genre":(.+?),', re.DOTALL).findall(entry)
        genre = match[0]
        match = re.compile('"url":"(.+?)","type":"(.+?)"', re.DOTALL).findall(entry)
        for url, type in match:
            urlTemp = urlMain+url+"includes/"+type.replace('-', '').replace(' ', '').lower()+"/large.html"
            url = "plugin://screensaver.randomtrailers/?url="+urllib.quote_plus(urlTemp)
            filter = ["- JP Sub","Interview","- UK","- BR Sub","- FR","- IT","- AU","- MX","- MX Sub","- BR","- RU","- DE","- ES","- FR Sub","- KR Sub","- Russian","- French","- Spanish","- German","- Latin American Spanish","- Italian"]
            filtered = False
            for f in filter:
                if f in type:
                    filtered = True
            if do_clips=='false':
                if 'Clip' in type:
                    filtered = True
            if do_featurettes =='false':
                if 'Featurette' in type:
                    filtered = True
            if trailer_type==0:
                if releasedate < datetime.date.today() :filtered = True
            if genreCheck(genre) and checkRating(rating) and not filtered:
                trailers.append([title,url,type,rating,year,thumb,fanart,genre])
    return trailers
    
def getTrailers(genre):
    # get the raw JSON output
    trailerstring = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": {"properties": ["title", "lastplayed", "studio", "writer", "plot", "votes", "top250", "originaltitle", "director", "tagline", "fanart", "runtime", "mpaa", "rating", "thumbnail", "file", "year", "genre", "trailer"], "filter": {"field": "genre", "operator": "contains", "value": "%s"}}, "id": 1}' % genre)
    trailerstring = unicode(trailerstring, 'utf-8', errors='ignore')
    trailers = json.loads(trailerstring)    
    return trailers

def getFiles(path):
    trailers = []
    folders = []
    # multipath support
    if path.startswith('multipath://'):
        # get all paths from the multipath
        paths = path[12:-1].split('/')
        for item in paths:
            folders.append(urllib.unquote_plus(item))
    else:
        folders.append(path)
    for folder in folders:
        if xbmcvfs.exists(xbmc.translatePath(folder)):
            # get all files and subfolders
            dirs,files = xbmcvfs.listdir(folder)
            for item in files:
                if not os.path.join(folder,item) in played:
                    trailers.append(os.path.join(folder,item))
            for item in dirs:
                # recursively scan all subfolders
                trailers += getFiles(os.path.join(folder,item))
    return trailers
    
class blankWindow(xbmcgui.WindowXML):
    def onInit(self):
        pass
        
class movieWindow(xbmcgui.WindowXMLDialog):

    def onInit(self):
        global played
        global SelectedGenre
        global trailer
        global do_timeout
        global NUMBER_TRAILERS
        global trailercount
        random.shuffle(trailers["result"]["movies"])
        trailercount=0
        trailer=random.choice(trailers["result"]["movies"])
        while trailer["trailer"] in played:
            trailer=random.choice(trailers["result"]["movies"])
            trailercount=trailercount+1
            if trailercount == len(trailers):
                played=[]
            
        lastPlay = True
        if not trailer["lastplayed"] =='' and hide_watched == 'true':
            pd=time.strptime(trailer["lastplayed"],'%Y-%m-%d %H:%M:%S')
            pd = time.mktime(pd)
            pd = datetime.datetime.fromtimestamp(pd)
            lastPlay = datetime.datetime.now() - pd
            lastPlay = lastPlay.days
            if lastPlay > int(watched_days) or watched_days == '0':
                lastPlay = True
            else:
                lastPlay = False
        if  trailer["trailer"] != '' and lastPlay:
            NUMBER_TRAILERS = NUMBER_TRAILERS -1
            played.append(trailer["trailer"])
            xbmc.log('Plalyed Count = '+str(len(played)))
            if hide_info == 'false':
                w=infoWindow('script-DialogVideoInfo.xml',addon_path,'default')
                do_timeout=True
                w.doModal()
                do_timeout=False
                del w
                if exit_requested:
                    xbmc.Player().stop()
            else:
                xbmc.Player().play(trailer["trailer"])
                NUMBER_TRAILERS = NUMBER_TRAILERS -1
            self.getControl(30011).setLabel(trailer["title"] + ' - ' + str(trailer["year"]))
            if hide_title == 'false':
                self.getControl(30011).setVisible(True)
            else:
                self.getControl(30011).setVisible(False)
            while xbmc.Player().isPlaying():                
                xbmc.sleep(250)
        
        self.close()
        
    def onAction(self, action):
        ACTION_PREVIOUS_MENU = 10
        ACTION_BACK = 92
        ACTION_ENTER = 7
        ACTION_I = 11
        ACTION_LEFT = 1
        ACTION_RIGHT = 2
        ACTION_UP = 3
        ACTION_DOWN = 4
        ACTION_TAB = 18
        ACTION_M = 122
        
        xbmc.log('action  =' + str(action.getId()))
        
        global exit_requested
        global movie_file
        if action == ACTION_PREVIOUS_MENU or action == ACTION_LEFT or action == ACTION_BACK:
            xbmc.Player().stop()
            exit_requested = True
            self.close()

        if action == ACTION_RIGHT or action == ACTION_TAB:
            xbmc.Player().stop()
            
        if action == ACTION_ENTER:
            exit_requested = True
            xbmc.Player().stop()
            movie_file = trailer["file"]
            self.getControl(30011).setVisible(False)
            self.close()
            
        if action == ACTION_M:
            self.getControl(30011).setVisible(True)
            xbmc.sleep(2000)
            self.getControl(30011).setVisible(False)
        
        if action == ACTION_I or action == ACTION_UP:
            self.getControl(30011).setVisible(False)
            w=infoWindow('script-DialogVideoInfo.xml',addon_path,'default')
            w.doModal()
            if hide_title == 'false':
                self.getControl(30011).setVisible(True)
            else:
                self.getControl(30011).setVisible(False)
            
class trailerWindow(xbmcgui.WindowXMLDialog):

    def onInit(self):
        global played
        global NUMBER_TRAILERS
        global trailercount
        played = []
        random.shuffle(trailers)
        trailer=random.choice(trailers)
        while trailer in played:
            trailer=random.choice(trailers)
            trailercount=trailercount+1
            if trailercount == len(trailers):
                played=[]
        NUMBER_TRAILERS = NUMBER_TRAILERS -1
        xbmc.Player().play(trailer)
        played.append(trailer)
        title = xbmc.translatePath(trailer)
        title =os.path.basename(title)
        title =os.path.splitext(title)[0]
        self.getControl(30011).setVisible(False)
        self.getControl(30011).setLabel(title)
        if hide_title == 'false':
            self.getControl(30011).setVisible(True)
        else:
            self.getControl(30011).setVisible(False)
        while xbmc.Player().isPlaying():                
            xbmc.sleep(250)
        self.close()
        
    def onAction(self, action):
        ACTION_PREVIOUS_MENU = 10
        ACTION_BACK = 92
        ACTION_ENTER = 7
        ACTION_I = 11
        ACTION_LEFT = 1
        ACTION_RIGHT = 2
        ACTION_UP = 3
        ACTION_DOWN = 4
        ACTION_TAB = 18
        ACTION_M = 122
        
        global exit_requested
        if action == ACTION_PREVIOUS_MENU or action == ACTION_LEFT or action == ACTION_BACK:
            xbmc.Player().stop()
            exit_requested = True
            self.close()

        if action == ACTION_RIGHT or action == ACTION_TAB:
            xbmc.Player().stop()
                            
        if action == ACTION_M:
            self.getControl(30011).setVisible(True)
            xbmc.sleep(3000)
            self.getControl(30011).setVisible(False)
            
class videoWindow(xbmcgui.WindowXMLDialog):

    def onInit(self):
        global played
        global NUMBER_TRAILERS
        global trailercount
        random.shuffle(trailers)
        trailer=random.choice(trailers)
        #trailers.append([title,type,url,year,thumb,fanart,genre,rating])
        
        while trailer in played:
            trailer=random.choice(trailers)
            trailercount=trailercount+1
            if trailercount == len(trailers):
                played=[]        
        played.append(trailer)
        xbmc.Player().play(trailer[1])
        xbmc.sleep(250)
        if xbmc.Player().isPlayingVideo():
            title = trailer[0].encode('utf-8') + ' - ' + trailer[2] + ' - ' + trailer[3]
            self.getControl(30011).setVisible(False)
            self.getControl(30011).setLabel(title)
            if hide_title == 'false':
                self.getControl(30011).setVisible(True)
            else:
                self.getControl(30011).setVisible(False)
            NUMBER_TRAILERS = NUMBER_TRAILERS -1
        while xbmc.Player().isPlaying():                
            xbmc.sleep(250)
        self.close()
        
    def onAction(self, action):
        ACTION_PREVIOUS_MENU = 10
        ACTION_BACK = 92
        ACTION_ENTER = 7
        ACTION_I = 11
        ACTION_LEFT = 1
        ACTION_RIGHT = 2
        ACTION_UP = 3
        ACTION_DOWN = 4
        ACTION_TAB = 18
        ACTION_M = 122
        
        global exit_requested
        if action == ACTION_PREVIOUS_MENU or action == ACTION_LEFT or action == ACTION_BACK:
            xbmc.Player().stop()
            exit_requested = True
            self.close()

        if action == ACTION_RIGHT or action == ACTION_TAB:
            xbmc.Player().stop()
                            
        if action == ACTION_M:
            self.getControl(30011).setVisible(True)
            xbmc.sleep(3000)
            self.getControl(30011).setVisible(False)
                        
class infoWindow(xbmcgui.WindowXMLDialog):

    def onInit(self):
        self.getControl(30001).setImage(trailer["thumbnail"])
        self.getControl(30003).setImage(trailer["fanart"])
        self.getControl(30002).setLabel(trailer["title"])
        self.getControl(30012).setLabel(trailer["tagline"])
        self.getControl(30004).setLabel(trailer["originaltitle"])
        directors = trailer["director"]
        movieDirector=''
        for director in directors:
            movieDirector = movieDirector + director + ', '
            if not movieDirector =='':
                movieDirector = movieDirector[:-2]
        self.getControl(30005).setLabel(movieDirector)
        writers = trailer["writer"]
        movieWriter=''
        for writer in writers:
            movieWriter = movieWriter + writer + ', '
            if not movieWriter =='':
                movieWriter = movieWriter[:-2]
        self.getControl(30006).setLabel(movieWriter)
        strImdb=''
        if not trailer["top250"] == 0:
            strImdb = ' - IMDB Top 250:' + str(trailer["top250"]) 
        self.getControl(30007).setLabel(str(round(trailer["rating"],2)) + ' (' + str(trailer["votes"]) + ' votes)' + strImdb)
        self.getControl(30009).setText(trailer["plot"])
        movieStudio=''
        studios=trailer["studio"]
        for studio in studios:
            movieStudio = movieStudio + studio + ', '
            if not movieStudio =='':
                movieStudio = movieStudio[:-2]
        self.getControl(30010).setLabel(movieStudio + ' - ' + str(trailer["year"]))
        movieGenre=''
        genres = trailer["genre"]
        for genre in genres:
            movieGenre = movieGenre + genre + ' / '
        if not movieGenre =='':
            movieGenre = movieGenre[:-3]
        self.getControl(30011).setLabel(str(trailer["runtime"] / 60) + ' Minutes - ' + movieGenre)
        imgRating='ratings/notrated.png'
        if trailer["mpaa"].startswith('G'): imgRating='ratings/g.png'
        if trailer["mpaa"] == ('G'): imgRating='ratings/g.png'
        if trailer["mpaa"].startswith('Rated G'): imgRating='ratings/g.png'
        if trailer["mpaa"].startswith('PG '): imgRating='ratings/pg.png'
        if trailer["mpaa"] == ('PG'): imgRating='ratings/pg.png'
        if trailer["mpaa"].startswith('Rated PG'): imgRating='ratings/pg.png'
        if trailer["mpaa"].startswith('PG-13 '): imgRating='ratings/pg13.png'
        if trailer["mpaa"] == ('PG-13'): imgRating='ratings/pg13.png'
        if trailer["mpaa"].startswith('Rated PG-13'): imgRating='ratings/pg13.png'
        if trailer["mpaa"].startswith('R '): imgRating='ratings/r.png'
        if trailer["mpaa"] == ('R'): imgRating='ratings/r.png'
        if trailer["mpaa"].startswith('Rated R'): imgRating='ratings/r.png'
        if trailer["mpaa"].startswith('NC17'): imgRating='ratings/nc17.png'
        if trailer["mpaa"].startswith('Rated NC17'): imgRating='ratings/nc1.png'
        self.getControl(30013).setImage(imgRating)
        if do_timeout:
            xbmc.sleep(2500)
            xbmc.Player().play(trailer["trailer"])
            self.close()
        
    def onAction(self, action):
        ACTION_PREVIOUS_MENU = 10
        ACTION_BACK = 92
        ACTION_ENTER = 7
        ACTION_I = 11
        ACTION_LEFT = 1
        ACTION_RIGHT = 2
        ACTION_UP = 3
        ACTION_DOWN = 4
        ACTION_TAB = 18
        
        xbmc.log('action  =' + str(action.getId()))
        global do_timeout
        global exit_requested
        global movie_file
        if action == ACTION_PREVIOUS_MENU or action == ACTION_LEFT or action == ACTION_BACK:
            do_timeout=False
            xbmc.Player().stop()
            exit_requested=True
            self.close()
            
        if action == ACTION_I or action == ACTION_DOWN:
            self.close()
            
        if action == ACTION_RIGHT or action == ACTION_TAB:
            xbmc.Player().stop()
            self.close()

        if action == ACTION_ENTER:
            movie_file = trailer["file"]
            xbmc.Player().stop()
            exit_requested=True
            self.close()
        
    
class XBMCPlayer(xbmc.Player):
    def __init__( self, *args, **kwargs ):
        pass
    def onPlayBackStarted(self):
        pass
    
    def onPlayBackStopped(self):
        global exit_requested
        pass
        
def playVideo():
    global exit_requested
    global NUMBER_TRAILERS
    global trailercount
    exit_requested = False
    player = XBMCPlayer()
    DO_CURTIANS = addon.getSetting('do_animation')
    DO_EXIT = addon.getSetting('do_exit')
    NUMBER_TRAILERS =  int(addon.getSetting('number_trailers'))
    if DO_CURTIANS == 'true':
        player.play(open_curtain_path)
        while player.isPlaying():
            xbmc.sleep(250)
    trailercount = 0
    while not exit_requested:
        if NUMBER_TRAILERS == 0:
            while not exit_requested and not xbmc.abortRequested:
                myMovieWindow = videoWindow('script-trailerwindow.xml', addon_path,'default',)
                myMovieWindow.doModal()
                del myMovieWindow
        else:
            while NUMBER_TRAILERS > 0:
                myMovieWindow = videoWindow('script-trailerwindow.xml', addon_path,'default',)
                myMovieWindow.doModal()
                del myMovieWindow
                if exit_requested:
                    break
        if not exit_requested:
            if DO_CURTIANS == 'true':
                player.play(close_curtain_path)
                while player.isPlaying():
                    xbmc.sleep(250)
        exit_requested=True        
        
def playTrailers():
    global exit_requested
    global movie_file
    global NUMBER_TRAILERS
    global trailercount
    movie_file = ''
    exit_requested = False
    player = XBMCPlayer()
    #xbmc.log('Getting Trailers')
    DO_CURTIANS = addon.getSetting('do_animation')
    DO_EXIT = addon.getSetting('do_exit')
    NUMBER_TRAILERS =  int(addon.getSetting('number_trailers'))
    if DO_CURTIANS == 'true':
        player.play(open_curtain_path)
        while player.isPlaying():
            xbmc.sleep(250)
    trailercount = 0
    while not exit_requested:
        if NUMBER_TRAILERS == 0:
            while not exit_requested and not xbmc.abortRequested:
                myMovieWindow = movieWindow('script-trailerwindow.xml', addon_path,'default',)
                myMovieWindow.doModal()
                del myMovieWindow
        else:
            NUMBER_TRAILERS = NUMBER_TRAILERS + 1
            while NUMBER_TRAILERS > 0:
                myMovieWindow = movieWindow('script-trailerwindow.xml', addon_path,'default',)
                myMovieWindow.doModal()
                del myMovieWindow
                if exit_requested:
                    break
        if not exit_requested:
            if DO_CURTIANS == 'true':
                player.play(close_curtain_path)
                while player.isPlaying():
                    xbmc.sleep(250)
        exit_requested=True
    if not movie_file == '':
        xbmc.Player(0).play(movie_file)

def playPath():
    global exit_requested
    global NUMBER_TRAILERS
    global trailercount
    exit_requested = False
    player = XBMCPlayer()
    DO_CURTIANS = addon.getSetting('do_animation')
    DO_EXIT = addon.getSetting('do_exit')
    NUMBER_TRAILERS =  int(addon.getSetting('number_trailers'))
    if DO_CURTIANS == 'true':
        player.play(open_curtain_path)
        while player.isPlaying():
            xbmc.sleep(250)
    trailercount = 0
    while not exit_requested:
        if NUMBER_TRAILERS == 0:
            while not exit_requested and not xbmc.abortRequested:
                myMovieWindow = trailerWindow('script-trailerwindow.xml', addon_path,'default',)
                myMovieWindow.doModal()
                del myMovieWindow
        else:
            NUMBER_TRAILERS = NUMBER_TRAILERS + 1
            while NUMBER_TRAILERS > 0:
                myMovieWindow = trailerWindow('script-trailerwindow.xml', addon_path,'default',)
                myMovieWindow.doModal()
                del myMovieWindow
                if exit_requested:
                    break
        if not exit_requested:
            if DO_CURTIANS == 'true':
                player.play(close_curtain_path)
                while player.isPlaying():
                    xbmc.sleep(250)
        exit_requested=True
 
 
    
if not xbmc.Player().isPlaying():
    trailers = []
    filtergenre = False
     
    if do_multiple:
        if do_library == 'true':
            library_trailers = getTrailers("")
            library_trailers = library_trailers["result"]["movies"]
            for trailer in library_trailers:
                trailers.append([trailer['title'],trailer['trailer'],'Trailer',trailer['mpaa']])
        if do_folder == 'true' and path !='':
            folder_trailers = getFiles(path)
            for trailer in folder_trailers:
                title = xbmc.translatePath(trailer)
                title =os.path.basename(title)
                title =os.path.splitext(title)[0]   
                trailers.append([title,trailer,'trailer', ''])
        if do_itunes == 'true':
            itunes_trailers = getVideos()
            for trailer in itunes_trailers:
                trailers.append([trailer[0],trailer[1],trailer[2]])
    else:
        if do_library == 'true':
            if do_genre == 'true':
                filtergenre = askGenres()
        
            success = False
            if filtergenre:
                success, selectedGenre = selectGenre()

            if success:
                trailers = getTrailers(selectedGenre)
            else:
                trailers = getTrailers("")
                
        if do_folder == 'true' and path !='':
            trailers = getFiles(path)
            
        if do_itunes == 'true' and not do_multiple:
            trailers = getVideos()
    
    bs=blankWindow = blankWindow('script-BlankWindow.xml', addon_path,'default',)
    bs.show()
    if do_volume == 'true':
        muted = xbmc.getCondVisibility("Player.Muted")
        if not muted and volume == 0:
            xbmc.executebuiltin('xbmc.Mute()')
        else:
            xbmc.executebuiltin('XBMC.SetVolume('+str(volume)+')')   
    if do_multiple:
        playVideo()
    else:
        if do_library == 'true':
            playTrailers()
        if do_folder == 'true' and path !='':
            playPath()
        if do_itunes == 'true':
            playVideo()
    del bs
    if do_volume == 'true':
        muted = xbmc.getCondVisibility("Player.Muted")
        if muted and volume == 0:
            xbmc.executebuiltin('xbmc.Mute()')
        else:
            xbmc.executebuiltin('XBMC.SetVolume('+str(currentVolume)+')')        
else:
    xbmc.log('Exiting Random Trailers Screen Saver Something is playing!!!!!!')


    
