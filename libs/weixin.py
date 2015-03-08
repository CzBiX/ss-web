from concurrent.futures import ThreadPoolExecutor
import hashlib
import logging
import xml.etree.ElementTree as Et
import time

from tornado import gen, escape
from tornado.ioloop import IOLoop
from tornado.options import options
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

from libs.shadowsocks import Shadowsocks


__author__ = 'czbix'


class WeiXin:
    _FROM_USER_TAG = 'FromUserName'
    _TO_USER_TAG = 'ToUserName'
    _CREATE_TIME_TAG = 'CreateTime'
    _MSG_TYPE_TAG = 'MsgType'
    _CONTENT_TAG = 'Content'
    _EVENT_TAG = 'Event'
    _EVENT_KEY_TAG = 'EventKey'

    _CLICK_EVENT = 'CLICK'
    _SUBSCRIBE_EVENT = 'subscribe'
    _UNSUBSCRIBE_EVENT = 'unsubscribe'
    _TEMPLATE_SEND_EVENT = 'TEMPLATESENDJOBFINISH'

    _GET_PWD_EVENT_KEY = 'getPwd'

    _thread_pool = ThreadPoolExecutor(1)

    def __init__(self, request_handler):
        self.handler = request_handler

    @staticmethod
    def check_sign(request_handler):
        timestamp = request_handler.get_query_argument('timestamp')
        nonce = request_handler.get_query_argument('nonce')
        signature = request_handler.get_query_argument('signature')

        calc_sign = hashlib.sha1(''.join(sorted([options.wx_token, timestamp, nonce])).encode()).hexdigest()

        return signature == calc_sign

    def handle_msg(self):
        tree = Et.fromstring(self.handler.request.body)

        from_user = tree.find(self._FROM_USER_TAG).text
        to_user = tree.find(self._TO_USER_TAG).text
        msg_type = tree.find(self._MSG_TYPE_TAG).text
        create_time = int(tree.find(self._CREATE_TIME_TAG).text)

        if msg_type == 'text' and self._handle_text_msg(tree, from_user, to_user):
            return
        elif msg_type == 'event' and self._handle_event_msg(tree, from_user, to_user):
            return
        else:
            logging.debug('received unknown msg, msg_type: ' + msg_type)

        self._unknown_msg(from_user, to_user)

    @classmethod
    def _handle_text_msg(cls, tree, from_user, to_user):
        content = tree.find(cls._CONTENT_TAG).text
        logging.debug('received text msg, content: ' + content)

        return False

    @staticmethod
    def _build_ss_info():
        ss = Shadowsocks.find_latest(Shadowsocks.workers)
        if not ss.running:
            ss.start()

        content = 'Id: %d\n' \
                  'Port: %d\n' \
                  'Password: %s' \
                  % (ss.index, ss.port, ss.password)

        return content

    @staticmethod
    def build_template_msg(ss, to_user):
        data = {
            'touser': to_user,
            'template_id': options.wx_template_id,
            'data': {
                'index': {
                    'value': ss.index,
                },
                'port': {
                    'value': ss.port,
                },
                'password': {
                    'value': ss.password,
                },
            }
        }

        return escape.json_encode(data)

    def _handle_event_msg(self, tree, from_user, to_user):
        event = tree.find(self._EVENT_TAG).text
        if event == self._UNSUBSCRIBE_EVENT:
            # there is nothing we can do
            return True

        if event == self._TEMPLATE_SEND_EVENT:
            # there is nothing we need to do
            return True

        if event == self._SUBSCRIBE_EVENT:
            self.handler.write(self._build_text_reply(to_user, from_user, '谢谢关注喵~'))
            return True

        if event == self._CLICK_EVENT:
            event_key = tree.find(self._EVENT_KEY_TAG).text
            if event_key == self._GET_PWD_EVENT_KEY:
                self.handler.write(self._build_text_reply(to_user, from_user, self._build_ss_info()))
                return True

        return False

    def _unknown_msg(self, from_user, to_user):
        random_texts = ['What does the fox say',
                        'Do you want to build a snowman',
                        'Let it go',
                        'You belong with me',
                        'Just one last dance',
                        'If I were a boy',
                        'Nothing else I can say',
                        '恋は渾沌の隷也',
                        '残酷な天使のテーゼ',
                        '恋爱サーキュレーション',
                        'ワールドイズマイン']

        import random

        self.handler.write(self._build_text_reply(to_user, from_user, random.choice(random_texts)))

    @classmethod
    def _build_text_reply(cls, from_user, to_user, content):
        builder = Et.TreeBuilder()
        builder.start('xml')

        import time

        for tag, value in [(cls._TO_USER_TAG, to_user), (cls._FROM_USER_TAG, from_user),
                           (cls._CREATE_TIME_TAG, str(int(time.time()))), (cls._MSG_TYPE_TAG, 'text'),
                           (cls._CONTENT_TAG, content)]:
            builder.start(tag)
            builder.data(value)
            builder.end(tag)

        builder.end('xml')
        return Et.tostring(builder.close(), 'utf-8')

    @classmethod
    def send_ss_info(cls, ss):
        cls._thread_pool.submit(WeiXinApi.send_template_msg, ss)


class WeiXinApi:
    _API_BASE = 'https://api.weixin.qq.com/cgi-bin'

    _access_token = None
    _expire_time = -1

    @classmethod
    @gen.coroutine
    def _refresh_token(cls):
        url = '%s/token?grant_type=client_credential&appid=%s&secret=%s'\
              % (cls._API_BASE, options.wx_app_id, options.wx_secret)

        client = AsyncHTTPClient()
        response = yield client.fetch(url)

        data = escape.json_decode(response.body)

        if 'errcode' in data:
            logging.warning('refresh token failed, code: %d, msg: %s' % (data['errcode'], data['errmsg']))
            raise IOError('get token failed')

        cls._access_token = data['access_token']
        cls._expire_time = time.time() + data['expires_in']

    @classmethod
    @gen.coroutine
    def _get_token(cls):
        if cls._access_token is None\
                or time.time() >= cls._expire_time:
            yield cls._refresh_token()

        return cls._access_token

    @classmethod
    @gen.coroutine
    def send_template_msg(cls, ss):
        token = yield cls._get_token()
        url = '%s/message/template/send?access_token=%s' % (cls._API_BASE, token)

        client = AsyncHTTPClient()

        for user in options.wx_users:
            msg = WeiXin.build_template_msg(ss, user)
            request = HTTPRequest(url, method='POST', body=msg)

            response = yield client.fetch(request)

            data = escape.json_decode(response.body)
            code = data['errcode']

            if code != 0:
                msg = data['errmsg']
                logging.warning('send template message failed: code: %d, msg: %s' % (code, msg))
                raise IOError('send template message failed')
