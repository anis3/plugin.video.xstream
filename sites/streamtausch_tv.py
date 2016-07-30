# -*- coding: utf-8 -*-
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib import logger
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.util import cUtil
import re

SITE_IDENTIFIER = 'streamtausch_tv'
SITE_NAME = 'StreamTausch'
SITE_ICON = 'streamtausch.png'

URL_MAIN = 'http://streamtausch.tv'
URL_Filme = URL_MAIN + '/stuff/'
URL_AktuelleFilme = URL_MAIN + '/stuff/online_film/23'
URL_SEARCH =  URL_MAIN + '/search/?q=%s'

def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_MAIN)
    oGui.addFolder(cGuiElement('Neue Filme online', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_AktuelleFilme)
    oGui.addFolder(cGuiElement('Aktuelle Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_Filme)
    oGui.addFolder(cGuiElement('Alle Filme', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showGenresList'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()

def showGenresList():
    oGui = cGui()
    params = ParameterHandler()
    sHtmlContent = cRequestHandler(URL_MAIN).request()
    aResult = cParser().parse(sHtmlContent, '<a[^>]*href="([^"]*)"[^>]*class="catName"><b>([^"<]+)')
    if aResult[0] and aResult[1][0]:
        total = len (aResult[1])
        for sUrl, sName in aResult[1]:      
            params.setParam('sUrl', sUrl)
            oGui.addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params, True, total)
    oGui.setEndOfDirectory()

def showEntries(entryUrl = False, sGui = False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    sHtmlContent = cRequestHandler(entryUrl).request()    
    pattern = '<table[^>]*class="eBlock"[^>]*>.*?'
    pattern += '<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?' # url / title
    pattern += '<img[^>]*src="([^"]*)"[^>]*>.*?' # img
    pattern += '(?:<fieldset[^>]*>.*?Jahr:</b>\s+(\d+).*?</fieldset>.*?)?' # year (opt)
    pattern += '</table>'
    aResult = cParser().parse(sHtmlContent, pattern)
    
    if aResult[0] and aResult[1][0]:
        total = len (aResult[1])
        for sUrl, sName, sThumbnail, sJahr in aResult[1]:
            oGuiElement = cGuiElement(cUtil().unescape(sName.decode('utf-8')).encode('utf-8'), SITE_IDENTIFIER, 'showHosters')
            oGuiElement.setSiteName(SITE_IDENTIFIER)
            oGuiElement.setThumbnail(sThumbnail if sThumbnail.startswith("http") else 'http:' + sThumbnail) 
            oGuiElement.setMediaType('movie')
            oGuiElement.setYear(sJahr)
            params.setParam('sName', sName)
            params.setParam('entryUrl', sUrl if sUrl.startswith("http") else URL_MAIN + sUrl)
            oGui.addFolder(oGuiElement, params, False, total)

    pattern = '<a[^>]*class="swchItem"[^>]*href="([^"]+)"[^>]*><span>&raquo;</span>'
    aResult = cParser().parse(sHtmlContent, pattern)
    if aResult[0] and aResult[1][0]:
       params.setParam('sUrl', URL_MAIN + aResult[1][0])
       oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)

    if not sGui:
        oGui.setView('movies')
        oGui.setEndOfDirectory()

def showSearchEntries(entryUrl = False, sGui = False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    sHtmlContent = cRequestHandler(entryUrl).request()
    pattern = '<div[^>]*align="center"[^>]*>'
    pattern += '<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?' # url / title
    pattern += '</div>'
    aResult = cParser().parse(sHtmlContent, pattern)
    
    if not aResult[0]:
        return
    
    total = len (aResult[1])
    for sEntryUrl, sName in aResult[1]:
        if "stuff" not in sEntryUrl: continue
        oGuiElement = cGuiElement(cUtil().unescape(sName.replace('<b>', '')).replace('</b>', '').decode('utf-8').encode('utf-8'), SITE_IDENTIFIER, 'showHosters')
        params.setParam('entryUrl', sEntryUrl)
        oGui.addFolder(oGuiElement, params, False, total)

def showHosters():
    oParams = ParameterHandler()
    sUrl = oParams.getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    sPattern = '<td[^>]*align="center"[^>]*valign="top"><a[^>]*href="([^"]+).*?src="/([^".]+)'
    aResult = cParser().parse(sHtmlContent, sPattern)
    hosters = []
    if aResult[1]:
        for sUrl, sName in aResult[1]:
            # diry fix for old iconnames
            if sName == 'putlocker':
                sName = 'vodlocker'
            elif sName == 'sockshare':   
                 sName = 'shared.sx'
            hoster = {}
            hoster['link'] = sUrl
            hoster['name'] = sName
            hosters.append(hoster)         
    if hosters:
       hosters.append('getHosterUrl')
    return hosters

def getHosterUrl(sUrl = False):
    if not sUrl: sUrl = ParameterHandler().getValue('url')
    results = []
    result = {}

    # resolve redirect
    if not sUrl.startswith("http"):
        oRequestHandler = cRequestHandler(URL_MAIN + sUrl)
        oRequestHandler.request()
        sUrl = oRequestHandler.getRealUrl()

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
    showSearchEntries(URL_SEARCH % sSearchText.strip(), oGui)
