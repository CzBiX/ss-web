import base64
import json
import string
import subprocess
import random

__author__ = 'czbix'


class Shadowsocks:
    def __init__(self):
        self._config = Shadowsocks._get_server_config()
        self._process = None
        """:type : subprocess.Popen"""

    @staticmethod
    def _get_server_config():
        with open("config.json") as data:
            return json.load(data)

    @property
    def config(self):
        return self._config

    @property
    def port(self):
        return self.config['server_port']

    @property
    def password(self):
        return self.config['password']

    @password.setter
    def password(self, value):
        self.config['password'] = value

    @property
    def method(self):
        return self.config['method']

    @property
    def fast_open(self):
        return self.config['fast_open']

    def start(self):
        assert not self.running

        args = [
            'ss-server',
            '-s', '0.0.0.0',
            '-p', str(self.port),
            '-k', self.password,
            '-m', self.method,
        ]
        if self.fast_open:
            args.append('--fast-open')

        self._process = subprocess.Popen(args)

    def new_password(self):
        password = Shadowsocks._get_new_password()
        self.password = password

    @staticmethod
    def _get_new_password():
        # noinspection PyUnusedLocal
        return ''.join([random.choice(string.ascii_letters + string.digits) for n in range(8)])

    @property
    def running(self):
        return (self._process is not None) and (self._process.poll() is None)

    def qrcode(self, server_addr):
        qrcode = "%s:%s@%s:%d" % (self.method, self.password, server_addr, self.port)
        return base64.b64encode(qrcode.encode()).decode()

    def stop(self):
        assert self._process is not None

        self._process.terminate()
        self._process.wait()

        self._process = None

    def __del__(self):
        if self.running:
            self.stop()
