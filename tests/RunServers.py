import http.server
import socketserver
from time import sleep
from threading import Thread
import socket
from contextlib import closing
import json


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def start_server(Handler, port):
    with socketserver.TCPServer(("", port), Handler) as httpd:
        print("Serving at port", port)
        httpd.serve_forever()


class ModifiedHandler(http.server.SimpleHTTPRequestHandler):
    sleep_time = []

    def __init__(self, *args, **kwargs):
        super(ModifiedHandler, self).__init__(*args, **kwargs)

    def log_message(self, format, *args):
        """Avoids printing every request handled."""
        pass


def do_HEAD(self):
    if self.__class__.timeout:
        sleep(10)
    return super(self.__class__, self).do_HEAD()


@classmethod
def change_timeout(cls):
    cls.timeout = not cls.timeout


def main():
    print("\nThis script will create and run HTTP servers on the localhost.")
    print('How many servers do you want to run? (Expected input: int between 1 and 5')

    while True:
        try:
            n_servers = int(input())
        except ValueError:
            pass
        else:
            if n_servers > 0 and n_servers < 6:
                break

    handlers = []
    count = 0
    json_file = {'websites': []}

    interval_time_list = [3, 7, 4, 9, 10]

    for i in range(n_servers):
        port = find_free_port()
        json_file['websites'].append({'name': 'Localhost {}'.format(i),
                                      'url': 'http://localhost:{}'.format(port),
                                      'interval': interval_time_list[i]})
        handlers.append(type('ModifiedHandler_{}'.format(count), (ModifiedHandler,), {'count': count,
                                                                                      'timeout': False,
                                                                                      'do_HEAD': do_HEAD,
                                                                                      'change_timeout': change_timeout}))
        thread = Thread(target=start_server, args=(handlers[-1], port,))
        thread.setDaemon(True)

        count += 1
        thread.start()
        sleep(1)

    path_to_new_json = "./../website_monitoring/file_to_import/test_import.json"

    with open(path_to_new_json, "w") as f:
        f.write(json.dumps(json_file))

    print("\nJSON created at {}.\n".format(path_to_new_json))

    while True:
        print('CURRENT STATE\n')
        for i, handler in enumerate(handlers):
            print("\t * Server {} -- Timeout: {}".format(i, handler.timeout))

        print("\nType the number of the server to change its status, or q to quit.")
        while True:
            try:
                handler_to_change = int(input())
            except ValueError:
                pass
            else:
                if handler_to_change < n_servers:
                    break

        handlers[handler_to_change].change_timeout()
        print('\n')


if __name__ == '__main__':
    main()
