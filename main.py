#!/usr/bin/python3

from tornado import ioloop
from tornado.httpserver import HTTPServer
from tornado.options import define
from tornado.web import Application, os, RequestHandler

from handlers.index import *
from handlers.qrcode import *
from handlers.user import *
from libs.shadowsocks import Shadowsocks


__author__ = 'czbix'

define("debug", default=True, type=bool)
define("login_password", default="bamboofun", type=str)
define("port", default=8000, help="port to listen", type=int)
define("cookie_secret", default="61oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o", help="key for HMAC", type=str)
define("password_timeout", default=7, help="auto reset ss password for days", type=int)
define("workers", default=3, help="the number of worker", type=int)


class App(Application):
    def __init__(self):
        current_path = os.path.dirname(__file__)
        settings = dict(
            debug=options.debug,
            template_path=os.path.join(current_path, "templates"),
            static_path=os.path.join(current_path, "static"),
            cookie_secret=options.cookie_secret,
            login_url='user/login',
        )

        handlers = [
            (r'/', IndexHandler),
            (r'/user/login', UserHandler),
            (r'/qrcode', QrcodeHandler),
        ]

        RequestHandler.set_default_headers = App._set_default_header
        self.shadowsocks = [Shadowsocks(i) for i in range(options.workers)]

        super(App, self).__init__(handlers, **settings)

        logging.info("listening on http://localhost:%s" % options.port)

        self.reset_timer = None
        if options.password_timeout > 0:
            self._reset_timer_callback()

    @staticmethod
    def _set_default_header(handler):
        handler.set_header('Server', 'Lover')

    def _reset_timer_callback(self):
        looper = ioloop.IOLoop.current()

        if self.reset_timer is not None:
            looper.remove_timeout(self.reset_timer)
            self.reset_timer = None

        oldest_worker = Shadowsocks.find_oldest(self.shadowsocks)

        if not oldest_worker.running:
            logging.info("no more running task, try later")
            looper.call_later(3600, self._reset_timer_callback)
            return

        oldest_time = oldest_worker.next_time

        from datetime import datetime

        left_time = oldest_time - datetime.now()
        if left_time.total_seconds() <= 0:
            logging.info("already timeout, reset password")
            self._reset_password(oldest_worker)
            return

        logging.info("schedule next call later %s" % left_time)
        self.reset_timer = looper.call_later(left_time.total_seconds(), self._reset_password)

    def _reset_password(self, oldest_worker=None):
        if oldest_worker is None:
            oldest_worker = Shadowsocks.find_oldest(self.shadowsocks)

        oldest_worker.new_password()
        if oldest_worker.running:
            oldest_worker.stop()

        oldest_worker.start()

        self._reset_timer_callback()


def main():
    options.parse_command_line()
    app = App()

    server = HTTPServer(app, xheaders=True)
    server.listen(options.port)

    ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
