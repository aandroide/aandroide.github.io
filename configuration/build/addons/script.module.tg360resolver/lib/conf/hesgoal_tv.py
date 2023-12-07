import re

from conf.common import CommonResolver


class HseGoalTv(CommonResolver):

    def find_page_src(self, src):
        try:
            ajax = re.compile(r"dtAjax = {\"url\":\"([^\"]+)\"", re.DOTALL).findall(src)[0].replace("\\/", "/")

            base = self.resolver.find_hostname(self.resolver.start_url)
            form_url = base + ajax

            if "www" not in form_url:
                form_url = form_url.replace("://", "://www.")

            form = \
            re.compile(r"<li id='.*?dooplay_player_option' data-type='([^']+)' data-post='(\d+)' data-nume='(\d+)'>",
                       re.DOTALL).findall(src)[0]
            ftype = form[0]
            fpost = form[1]
            fnume = form[2]

            data = {"action": "doo_player_ajax", "post": fpost, "nume": fnume, "type": ftype}
            return self.resolver.cli.post_request(form_url, data=data).text
        except Exception as e:
            import traceback
            traceback.print_stack()
            print(e)
            return None
