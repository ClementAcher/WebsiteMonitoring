import http.server
import socketserver
from time import sleep
from threading import Thread
import os, sys

PORT = 8000


class HiddenPrints:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
        # sys.stderr = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self._original_stdout
        # sys.stderr = self._original_stdout

class ModifiedHandler(http.server.SimpleHTTPRequestHandler):
    sleep_time = 0

    def set_sleep_time(self):
        pass

    def do_GET(self):
        sleep(self.__class__.sleep_time)
        return super(ModifiedHandler, self).do_GET()

    def do_HEAD(self):
        sleep(self.__class__.sleep_time)
        return super(ModifiedHandler, self).do_HEAD()


def start_server(Handler):
    with HiddenPrints():
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print("serving at port", PORT)
            httpd.serve_forever()


if __name__ == '__main__':
    Handler = ModifiedHandler

    thread = Thread(target=start_server, args=(Handler,))
    thread.start()

    timeout = False

    while True:
        if timeout:
            print("Press a key to stop timeout")
            input()
            Handler.sleep_time = 0
        else:
            print("Press a key to timeout")
            input()
            Handler.sleep_time = 10
        timeout = not timeout
