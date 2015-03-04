import base64
from datetime import datetime, timedelta
import json
import string
import subprocess
import random
from tornado.options import options

__author__ = 'czbix'


class Shadowsocks:
    CONFIG_FILE_NAME = 'config.json'

    workers = None
    """:type : list[Shadowsocks]"""

    def __init__(self, index, config):
        self._index = index
        self._config = config
        self._process = None
        """:type : subprocess.Popen"""
        self._next_time = None

        pwds = config['password']
        self._password = pwds[index if len(pwds) > index else 0]

    @classmethod
    def read_config(cls):
        with open(cls.CONFIG_FILE_NAME) as file:
            data = json.load(file)

        if isinstance(data['password'], str):
            data['password'] = [data['password']]

        if 'running' not in data:
            data['running'] = []

        return data

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
        return self._password

    @password.setter
    def password(self, value):
        self._password = value

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
        self._next_time = datetime.now() + timedelta(days=options.password_timeout)

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
    def next_time(self):
        return datetime.max if (self._next_time is None) else self._next_time

    def qrcode(self, server_addr):
        qrcode = '%s:%s@%s:%d' % (self.method, self.password, server_addr, self.port)
        return base64.b64encode(qrcode.encode()).decode()

    def stop(self):
        if self._process is None:
            return

        self._process.terminate()
        self._process.wait()

        self._process = None
        self._next_time = None

    @staticmethod
    def find_oldest(workers):
        """
        :rtype: libs.shadowsocks.Shadowsocks
        """
        assert len(workers) > 0

        return min(workers, key=lambda ss: ss.next_time)

    @staticmethod
    def find_latest(workers):
        """
        :rtype: libs.shadowsocks.Shadowsocks
        """
        assert len(workers) > 0

        return max(workers, key=lambda ss: ss.next_time)

    @classmethod
    def save_config(cls, workers):
        running = []
        pwd_list = []
        for ss in workers:
            if ss.running:
                running.append(ss.index)

            pwd_list.append(ss.password)

        with open(cls.CONFIG_FILE_NAME, mode='r+') as file:
            import json

            data = json.load(file)
            data['password'] = pwd_list
            data['running'] = running

            file.truncate(0)
            file.seek(0)
            json.dump(data, file)

    def __del__(self):
        if self.running:
            self.stop()
