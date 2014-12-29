import json
import tornado
from tornado.web import RequestHandler

__author__ = 'czbix'


class BaseHandler(RequestHandler):
    def initialize(self):
        self.set_header('Server', 'Lover')

    def get_current_user(self):
        return self.get_cookie('login') == '1'

    def write_json(self, data):
        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps(data))

    def write_png(self, data):
        self.set_header('Content-Type', 'image/png')
        self.write(data)