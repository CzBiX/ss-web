import hashlib
from handlers.base import BaseHandler

__author__ = 'czbix'


class WeiXinHandler(BaseHandler):
    def get(self):
        echostr = self.get_query_argument('echostr')

        if not self.check_sign():
            self.send_error()
            return

        self.write(echostr)

    def check_sign(self):
        token = self.get_query_argument('token')
        timestamp = self.get_query_argument('timestamp')
        nonce = self.get_query_argument('nonce')
        signature = self.get_query_argument('signature')

        calc_sign = hashlib.sha1(str.join(sorted([token, timestamp, nonce]))).hexdigest()

        return signature == calc_sign


