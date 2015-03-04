from tornado.options import options
from tornado.web import HTTPError
from .base import BaseHandler

__author__ = 'czbix'


class UserHandler(BaseHandler):
    def get(self):
        if self.current_user:
            self.redirect('/')

        self.render('user/login.html')

    def post(self):
        if self.get_body_argument('password') != options.login_password:
            raise HTTPError(500)

        self.set_secure_cookie('login', '1')
        self.redirect(self.get_query_argument('next'))
