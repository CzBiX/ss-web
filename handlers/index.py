import json
from time import sleep
from handlers.base import BaseHandler
from tornado.web import authenticated

__author__ = 'czbix'


class IndexHandler(BaseHandler):
    @authenticated
    def get(self):
        ss = self.get_ss()
        self.render("index.html", config=(
            ('Port', ss.port),
            ('Password', ss.password),
            ('Method', ss.method),
            ('Fast Open', ss.fast_open),
        ), running=str(ss.running).lower())

    @authenticated
    def post(self):
        ss = self.get_ss()
        action = self.get_body_argument('action')
        if action == 'start':
            ss.start()
            sleep(1)
        elif action == 'stop':
            ss.stop()
        elif action == 'new_password':
            ss.new_password()
            if ss.running:
                ss.stop()

        result = {
            'running': ss.running,
        }

        self.write_json(result)

    def get_ss(self):
        """

        :rtype : libs.shadowsocks.Shadowsocks
        """
        return self.application.shadowsocks
