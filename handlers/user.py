from .base import BaseHandler

__author__ = 'czbix'


class UserHandler(BaseHandler):
    def get(self):
        if self.current_user:
            self.redirect('/')

        self.render('user/login.html')

    def post(self):
        if self.get_body_argument('password') != 'bamboofun':
            self.send_error(500)

        self.set_cookie('login', '1', expires_days=7)
        self.redirect(self.get_query_argument('next'))
