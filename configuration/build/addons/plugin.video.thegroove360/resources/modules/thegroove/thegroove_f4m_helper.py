import threading
import _thread as thread
import xbmcgui
import xbmc
from F4mProxy import f4mProxy
from F4mProxy import MyPlayer


class TGf4mProxyHelper():
    def playF4mLink(self, url, item, proxy=None, use_proxy_for_chunks=False, maxbitrate=0, simpleDownloader=False,
                    auth=None, streamtype='HDS', setResolved=False, swf=None, callbackpath="", callbackparam="",
                    referer="", origin="", cookie="", iconImage="DefaultVideo.png"):
        try:
            # print "URL: " + url
            stopPlaying = threading.Event()
            progress = xbmcgui.DialogProgress()
            import checkbad
            checkbad.do_block_check(False)

            f4m_proxy = f4mProxy()
            stopPlaying.clear()
            runningthread = thread.start_new_thread(f4m_proxy.start, (stopPlaying,))
            # progress.create('Conectando...')
            progress.create('F4mProxy', 'Connetendo...')
            stream_delay = 1
            # progress.update( 20, "", 'Aguarde...', "" )
            xbmc.sleep(stream_delay * 1000)
            # progress.update( 100, "", 'Carregando transmissão...', "" )
            progress.update(100, 'Cariacamento streaming...')
            url_to_play = f4m_proxy.prepare_url(url, proxy, use_proxy_for_chunks, maxbitrate=maxbitrate,
                                                simpleDownloader=simpleDownloader, auth=auth, streamtype=streamtype,
                                                swf=swf, callbackpath=callbackpath, callbackparam=callbackparam,
                                                referer=referer, origin=origin, cookie=cookie)
            # listitem = xbmcgui.ListItem(name,path=url_to_play, iconImage=iconImage, thumbnailImage=iconImage)
            listitem = xbmcgui.ListItem(item.label, path=url_to_play)
            listitem.setInfo('video', {'Title': item.label})
            listitem.setArt({"icon": "DefaultVideo.png", "thumb": iconImage})
            try:
                if streamtype == None or streamtype == '' or streamtype in ['HDS'  'HLS', 'HLSRETRY']:
                    listitem.setMimeType("flv-application/octet-stream")
                    listitem.setContentLookup(False)
                elif streamtype in ('TSDOWNLOADER'):
                    listitem.setMimeType("video/mp2t")
                    listitem.setContentLookup(False)
                elif streamtype in ['HLSREDIR']:
                    listitem.setMimeType("application/vnd.apple.mpegurl")
                    listitem.setContentLookup(False)
            except:
                pass
                # print 'error while setting setMimeType, so ignoring it '

            if setResolved:
                return url_to_play, listitem
            mplayer = MyPlayer()
            mplayer.stopPlaying = stopPlaying
            progress.close()
            mplayer.play(url_to_play, listitem)

            # xbmc.Player().play(url, listitem)
            firstTime = True
            played = False
            while True:
                if stopPlaying.isSet():
                    break
                if xbmc.Player().isPlaying():
                    played = True
                xbmc.log('Sleeping...')
                xbmc.sleep(200)
                # if firstTime:
                #    xbmc.executebuiltin('Dialog.Close(all,True)')
                #    firstTime=False
                # stopPlaying.isSet()

                # print 'Job done'
            return played
        except:
            return False
