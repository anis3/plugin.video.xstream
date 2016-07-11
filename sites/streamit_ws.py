# -*- coding: utf-8 -*-
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib import logger
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.pluginHandler import cPluginHandler
from resources.lib.util import cUtil
import re

SITE_IDENTIFIER = 'streamit_ws'
SITE_NAME = 'StreamIT'
SITE_ICON = 'streamit.png'

URL_MAIN = 'http://streamit.ws/'
URL_Kinofilme = URL_MAIN + 'kino'
URL_Filme = URL_MAIN + 'film'
URL_HDFilme = URL_MAIN + 'film-hd'
URL_SEARCH =  URL_MAIN + 'suche/?s=%s'
URL_Serie = URL_MAIN + 'serie'

def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_Kinofilme)
    oGui.addFolder(cGuiElement('Kino Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_Filme)
    oGui.addFolder(cGuiElement('Neue Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_HDFilme)
    oGui.addFolder(cGuiElement('HD Filme', SITE_IDENTIFIER, 'showEntries'), params)  
    params.setParam('sUrl', URL_MAIN + '/genre-film')
    oGui.addFolder(cGuiElement('Genre Filme', SITE_IDENTIFIER, 'showGenre'), params)
    params.setParam('sUrl', URL_MAIN + '/genre-serie')
    oGui.addFolder(cGuiElement('Genre Serien', SITE_IDENTIFIER, 'showGenre'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()
    
def showGenre(entryUrl = False):
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oGui = cGui()
    sHtmlContent = cRequestHandler(entryUrl).request()
    aResult = cParser().parse(sHtmlContent, '<h1>Genre.*?</h1>.*?</div>')
    if aResult[0]:
        sHtmlContent = aResult[1][0]
    pattern = '<li><a[^>]href="([^"]+)">([^"<]+)' # url / title
    aResult = cParser().parse(sHtmlContent, pattern)
    for sUrl, sTitle in aResult[1]:
        params.setParam('sUrl', (URL_MAIN + sUrl))
        oGui.addFolder(cGuiElement(cUtil().unescape(sTitle.decode('utf-8')).encode('utf-8'), SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()
    
def showEntries(entryUrl = False, sGui = False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    sHtmlContent = cRequestHandler(entryUrl).request()
    pattern ='<div class="cover"><a[^>]*href="([^"]+)" title="([^"]+).*?data-src="([^"]+)'
    aResult = cParser().parse(sHtmlContent, pattern)
    if len(aResult) > 0:
        for sUrl, sName, sThumbnail in aResult[1]:
            oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
            oGuiElement.setSiteName(SITE_IDENTIFIER)
            oGuiElement.setThumbnail(URL_MAIN + sThumbnail)
            oGuiElement.setMediaType('movie')
            params.setParam('entryUrl', URL_MAIN + sUrl)
            params.setParam('sName', sName)
            params.setParam('sThumbnail', sThumbnail)
            oGui.addFolder(oGuiElement, params, bIsFolder = False,)
            oGui.setView('movies')
    pattern = '<a[^>]href=[^>]([^">]+)[^>]>Next'
    aResult = cParser().parse(sHtmlContent, pattern)
    if aResult[0] and aResult[1][0]:
       params.setParam('sUrl', entryUrl + aResult[1][0])
       oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
    if not sGui:
	    oGui.setEndOfDirectory()
    return

def showHosters():
    oParams = ParameterHandler()
    sUrl = oParams.getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    aResult = cParser().parse(sHtmlContent, '<div[^>]class="mirrors.*?<div[^>]id="content">') # filter main content if needed
    if aResult[0]:
        sHtmlContent = aResult[1][0]    
    sPattern = '<a href="([^"]+).*?name="save"[^>]value="([^"[1-9]+)' # url / hostername
    aResult = cParser().parse(sHtmlContent, sPattern)
    hosters = []
    if aResult[1]:
        for sUrl, sName in aResult[1]:
            sHtmlContent = cRequestHandler(sUrl).request()
            Pattern = 'none"><a[^>]*href="([^"]+)'
            bResult = cParser().parse(sHtmlContent, Pattern)
            if bResult[1]:    
                for Url in bResult[1]:
                    hoster = {}
                    hoster['name'] = sName.strip()
                    hoster['link'] = Url.lower()
                    oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
                    hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters		
	
def getHosterUrl(sUrl = False):
    if not sUrl: sUrl = ParameterHandler().getValue('url')
    results = []
    result = {}
    result['streamUrl'] = sUrl
    result['resolved'] = False
    results.append(result)
    return results

def showSearch():
    oGui = cGui()
    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    oGui.setEndOfDirectory()

def _search(oGui, sSearchText):
    if not sSearchText: return
    showEntries(URL_SEARCH % sSearchText.strip(), oGui)