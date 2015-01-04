from time import sleep
from handlers.base import BaseHandler
from tornado.web import authenticated

__author__ = 'czbix'


class IndexHandler(BaseHandler):
    @authenticated
    def get(self):
        ss = self._get_ss()
        running = str(ss.running).lower()
        qrcode = ss.qrcode(self._get_host())
        self.render("index.html", config=ss, running=running, qrcode=qrcode)

    @authenticated
    def post(self):
        ss = self._get_ss()
        action = self.get_body_argument('action')
        if action == 'start':
            ss.start()
            sleep(1)
        elif action == 'stop':
            ss.stop()
        elif action == 'new_password':
            if self._get_reset_timer() is not None:
                self._get_reset_timer().stop()
                self._get_reset_timer().start()

            ss.new_password()
            if ss.running:
                ss.stop()

        result = {
            'running': ss.running,
            'password': ss.password,
            'qrcode': ss.qrcode(self._get_host()),
        }

        self.write_json(result)

    def _get_ss(self):
        """
        :rtype: libs.shadowsocks.Shadowsocks
        """
        return self.application.shadowsocks

    def _get_reset_timer(self):
        """
        :rtype: tornado.ioloop.PeriodicCallback
        """
        return self.application.reset_timer

    def _get_host(self):
        return self.request.host.lower().split(':')[0]
