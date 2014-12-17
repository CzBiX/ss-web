#!/usr/bin/python3

import tornado
import logging

from tornado import ioloop
from tornado.httpserver import HTTPServer
from tornado.ioloop import PeriodicCallback
from tornado.options import define, options
from tornado.web import Application, os, RequestHandler
from handlers.index import IndexHandler
from handlers.user import *
from libs.shadowsocks import Shadowsocks

__author__ = 'czbix'

define("debug", default=True, type=bool)
define("port", default=8000, help="port to listen", type=int)
define("cookie_secret", default="61oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o", help="key for HMAC", type=str)


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
        ]

        RequestHandler.set_default_headers = App._set_default_header
        self.shadowsocks = Shadowsocks()

        super(App, self).__init__(handlers, **settings)
        #PeriodicCallback(None, 1000).start()

        logging.info("listening on http://localhost:%s" % options.port)

    @staticmethod
    def _set_default_header(handler):
        handler.set_header('Server', 'Lover')


def main():
    options.parse_command_line()
    app = App()

    server = HTTPServer(app)
    server.listen(options.port)

    ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
