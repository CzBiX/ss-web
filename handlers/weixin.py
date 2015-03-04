import hashlib
import logging
import xml.etree.ElementTree as Et
from tornado.web import HTTPError
from handlers.base import BaseHandler

__author__ = 'czbix'


class WeiXinHandler(BaseHandler):
    FROM_USER_TAG = 'FromUserName'
    TO_USER_TAG = 'ToUserName'
    CREATE_TIME_TAG = 'CreateTime'
    MSG_TYPE_TAG = 'MsgType'
    CONTENT_TAG = 'Content'

    # TODO: token should be configurable
    TOKEN = 'wxpush'

    def prepare(self):
        if not self.settings['debug'] and not self._check_sign():
            raise HTTPError(401, 'invalid signature')

    def get(self):
        echostr = self.get_query_argument('echostr')
        self.write(echostr)

    def _check_sign(self):
        timestamp = self.get_query_argument('timestamp')
        nonce = self.get_query_argument('nonce')
        signature = self.get_query_argument('signature')

        calc_sign = hashlib.sha1(''.join(sorted([self.TOKEN, timestamp, nonce])).encode()).hexdigest()

        return signature == calc_sign

    def post(self):
        tree = Et.fromstring(self.request.body)

        from_user = tree.find(self.FROM_USER_TAG).text
        to_user = tree.find(self.TO_USER_TAG).text
        msg_type = tree.find(self.MSG_TYPE_TAG).text
        # create_time = tree.find(self.CREATE_TIME_TAG).text

        if msg_type == 'text':
            content = tree.find(self.CONTENT_TAG).text
            logging.debug('received text msg, content: ' + content)
            self._unknown_data(from_user, to_user)
        else:
            logging.debug('received unknown msg, msg_type: ' + msg_type)
            self._unknown_data(from_user, to_user)

    def _unknown_data(self, from_user, to_user):
        self.write(self._build_text_reply(to_user, from_user, 'What does the fox say?'))

    @classmethod
    def _build_text_reply(cls, from_user, to_user, content):
        builder = Et.TreeBuilder()
        builder.start('xml')

        import time

        for tag, value in [(cls.TO_USER_TAG, to_user), (cls.FROM_USER_TAG, from_user),
                           (cls.CREATE_TIME_TAG, str(int(time.time()))), (cls.MSG_TYPE_TAG, 'text'),
                           (cls.CONTENT_TAG, content)]:
            builder.start(tag)
            builder.data(value)
            builder.end(tag)

        builder.end('xml')
        return Et.tostring(builder.close())

