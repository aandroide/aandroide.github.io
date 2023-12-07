from conf.common import CommonResolver


class Deliriousholistic(CommonResolver):

    def find_stream(self):
        return [r"var src=\"([^\"]+)\""]
