from time import sleep
from handlers.base import BaseHandler
from tornado.web import authenticated
from libs.shadowsocks import Shadowsocks

__author__ = 'czbix'


class IndexHandler(BaseHandler):
    @authenticated
    def get(self):
        if self.request.path == '/save':
            Shadowsocks.save_config(Shadowsocks.workers)
            self.write("OK!")
            return

        sid = self.get_query_argument('id', None)
        if sid is None:
            self.redirect('/?id=%d' % Shadowsocks.find_latest(Shadowsocks.workers).index)
            return

        ss = self._get_ss(sid)
        qrcode = ss.qrcode(self._get_host())
        self.render("index.html", config=ss, qrcode=qrcode, index=sid)

    @authenticated
    def post(self):
        sid = self.get_body_argument('id')
        action = self.get_body_argument('action')

        ss = self._get_ss(sid)
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
            'password': ss.password,
            'qrcode': ss.qrcode(self._get_host()),
            'nextTime': ss.next_time.timestamp(),
        }

        self.write_json(result)

    @staticmethod
    def _get_ss(index):
        """
        :rtype: libs.shadowsocks.Shadowsocks
        """
        return Shadowsocks.workers[int(index)]

    def _get_reset_timer(self):
        """
        :rtype: tornado.ioloop.PeriodicCallback
        """
        return self.application.reset_timer

    def _get_host(self):
        from tornado import httputil

        return httputil.split_host_and_port(self.request.host)[0]
