import hashlib
from handlers.base import BaseHandler

__author__ = 'czbix'


class WeiXinHandler(BaseHandler):
    TOKEN = 'wxpush'

    def get(self):
        echostr = self.get_query_argument('echostr')

        if not self._check_sign():
            self.send_error()
            return

        self.write(echostr)

    def _check_sign(self):
        timestamp = self.get_query_argument('timestamp')
        nonce = self.get_query_argument('nonce')
        signature = self.get_query_argument('signature')

        calc_sign = hashlib.sha1(''.join(sorted([self.TOKEN, timestamp, nonce])).encode()).hexdigest()

        return signature == calc_sign
