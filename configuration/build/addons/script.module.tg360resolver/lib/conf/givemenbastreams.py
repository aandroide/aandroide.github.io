from conf.common import CommonResolver


class GiveMeNbaStreams(CommonResolver):

    def find_stream(self):
        return [r"source: '([^']+)'"]
