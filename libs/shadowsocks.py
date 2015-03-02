import base64
from datetime import datetime
import json
import string
import subprocess
import random

__author__ = 'czbix'


class Shadowsocks:
    def __init__(self, index):
        self._index = index
        self._config = Shadowsocks._get_server_config()
        self._process = None
        """:type : subprocess.Popen"""
        self._start_time = None

    @staticmethod
    def _get_server_config():
        with open("config.json") as data:
            return json.load(data)

    @property
    def index(self):
        return self._index

    @property
    def config(self):
        return self._config

    @property
    def port(self):
        return self.config['server_port'] + self.index

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
        self._start_time = datetime.now()

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

    @property
    def start_time(self):
        return datetime.max if (self._start_time is None) else self._start_time

    def qrcode(self, server_addr):
        qrcode = "%s:%s@%s:%d" % (self.method, self.password, server_addr, self.port)
        return base64.b64encode(qrcode.encode()).decode()

    def stop(self):
        if self._process is None:
            return

        self._process.terminate()
        self._process.wait()

        self._process = None
        self._start_time = None

    @staticmethod
    def find_oldest(workers):
        """
        :rtype: libs.shadowsocks.Shadowsocks
        """
        assert len(workers) > 0

        return min(workers, key=lambda ss: ss.start_time)

    @staticmethod
    def find_latest(workers):
        """
        :rtype: libs.shadowsocks.Shadowsocks
        """
        assert len(workers) > 0

        return max(workers, key=lambda ss: ss.start_time)

    def __del__(self):
        if self.running:
            self.stop()
