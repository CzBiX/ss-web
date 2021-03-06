#!/usr/bin/python3
import sys
import logging

from tornado import ioloop
from tornado.httpserver import HTTPServer
from tornado.options import define, options
from tornado.web import Application, os, RequestHandler

from handlers.index import IndexHandler
from handlers.qrcode import QrcodeHandler
from handlers.user import UserHandler
from handlers.weixin import WeiXinHandler
from libs.shadowsocks import Shadowsocks
from libs.weixin import WeiXin

__author__ = 'czbix'

define("login_password", type=str)
define("workers", default=3, help="the number of worker", type=int)
define('wx_token', help='the token used for weixin', type=str)
define('wx_template_id', type=str)
define('wx_users', type=list)
define('wx_app_id', type=str)
define('wx_secret', type=str)

define("debug", default=False, type=bool)
define("port", default=8000, help="port to listen", type=int)
define("cookie_secret", default="61oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o", help="key for HMAC", type=str)
define("password_timeout", default=7, help="auto reset ss password for days", type=int)


class App(Application):
    def __init__(self):
        current_path = os.path.dirname(__file__)
        settings = dict(
            debug=options.debug,
            autoreload=True,
            template_path=os.path.join(current_path, "templates"),
            static_path=os.path.join(current_path, "static"),
            cookie_secret=options.cookie_secret,
            login_url='user/login',
        )

        handlers = [
            (r'/', IndexHandler),
            (r'/save', IndexHandler),
            (r'/user/login', UserHandler),
            (r'/qrcode', QrcodeHandler),
        ]

        if options.wx_token is None:
            logging.info('wx_token is not configured')
        else:
            handlers.append((r'/weixin', WeiXinHandler))

        if options.wx_app_id is None or options.wx_secret is None or options.wx_template_id is None:
            logging.info('wx_app_id/wx_secret/wx_template_id is not configured')
        else:
            Shadowsocks.add_password_callback(lambda ss: WeiXin.send_ss_info(ss))

        RequestHandler.set_default_headers = App._set_default_header

        try:
            ss_config = Shadowsocks.read_config()
        except FileNotFoundError as e:
            print('can\'t found ' + e.filename)
            sys.exit(e.errno)

        Shadowsocks.workers = [Shadowsocks(i, ss_config) for i in range(options.workers)]
        for index in ss_config['running']:
            Shadowsocks.workers[index].start()

        super(App, self).__init__(handlers, **settings)

        logging.info("listening on http://localhost:%s" % options.port)

        self.reset_timer = None
        if options.password_timeout > 0:
            self._reset_timer_callback()

        from tornado import autoreload

        autoreload.add_reload_hook(App._stop_all_worker)

    @staticmethod
    def _stop_all_worker():
        Shadowsocks.save_config(Shadowsocks.workers)

        for ss in Shadowsocks.workers:
            ss.stop()

    @staticmethod
    def _set_default_header(handler):
        handler.set_header('Server', 'Lover')

    def _reset_timer_callback(self):
        looper = ioloop.IOLoop.current()

        if self.reset_timer is not None:
            looper.remove_timeout(self.reset_timer)
            self.reset_timer = None

        oldest_worker = Shadowsocks.find_oldest(Shadowsocks.workers)

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
            oldest_worker = Shadowsocks.find_oldest(Shadowsocks.workers)

        oldest_worker.new_password(is_manual=False)
        if oldest_worker.running:
            oldest_worker.stop()

        oldest_worker.start()

        self._reset_timer_callback()


SERVER_CONF_NAME = 'server.conf'


def main():
    if os.path.isfile(SERVER_CONF_NAME):
        options.parse_config_file(SERVER_CONF_NAME)

    options.parse_command_line()

    if options.login_password is None:
        print('please configure login password first')
        sys.exit(-1)

    app = App()

    server = HTTPServer(app, xheaders=True)
    server.listen(options.port)

    try:
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        print('Exit by KeyboardInterrupt')


if __name__ == "__main__":
    main()
