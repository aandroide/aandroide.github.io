from conf.common import CommonResolver


class LiveSport365(CommonResolver):

    def find_stream(self):
        return [r"file:.*?[\'|\"]([^\'|\"]+)\sor"]
