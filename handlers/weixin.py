import logging

from tornado.options import options
from tornado.web import HTTPError

from handlers.base import BaseHandler
from libs.weixin import WeiXin

__author__ = 'czbix'


class WeiXinHandler(BaseHandler):
    def prepare(self):
        if not WeiXin.check_sign(self):
            if options.debug:
                logging.warning('invalid signature')
            else:
                raise HTTPError(401, 'invalid signature')

    def get(self):
        echostr = self.get_query_argument('echostr')
        self.write(echostr)

    def post(self):
        weixin = WeiXin(self)
        weixin.handle_msg()
