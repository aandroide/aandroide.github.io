from conf.common import CommonResolver


class Mediafire(CommonResolver):

    def find_stream(self):
        return [r"window.location.href = '(http.*?://.*?.mediafire.com/.*?)'"]
