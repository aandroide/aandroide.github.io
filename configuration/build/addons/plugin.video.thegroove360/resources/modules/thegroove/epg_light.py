from resources.modules.thegroove.epg import Epg


class EpgLight(Epg, object):

    def __init__(self, progress=False, bg=True):
        super(EpgLight, self).__init__(progress, bg)
        self.epg_url = "http://www.epg-guide.com/it.gz"


if __name__ == "__main__":
    epg = EpgLight()
    # epg.set_channels_names()
    print(epg.normalize_name("realtime"))
    # epg.set_logo_names()
    # epg.find_current_playing("dazn 1")
