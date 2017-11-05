import http.server
import socketserver
import os
from time import sleep
from threading import Thread
import socket
from contextlib import closing
import json
from random import random
from statistics import mean

# This script will create and run a number chosen by the user of servers on the localhost that can be controlled.
# The created servers can easily be set as running normally or as "fake" down server.
# A file to quickly import the servers is created in the WebsiteMonitoring/website_monitoring/file_to_import folder.

# Important note: the number of servers that can be created is limited to 5 because too many servers running at the
# same time led to "ConnectionError" while handling certain requests. Even with a mximum of 5 servers running at the
# same time, it might still happen from time to time. It is also the reason why the interval check time are
# "desynchronised" to avoid several requests to the localhost at the same time.
# This issue has nothing to do with the WebsiteMonitoring app, and might be solved by making the created servers even
# simpler.

PROBABILITY_OF_TIMEOUT = 0.2

def find_free_port():
    """ Returns a port that is not currently being used."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def start_server(Handler, port):
    """Start the server using the Handler class provided."""
    with socketserver.TCPServer(("", port), Handler) as httpd:
        print("Serving at port", port)
        httpd.serve_forever()


class ModifiedHandler(http.server.SimpleHTTPRequestHandler):
    """
    This class is simply used to override the log_message method to avoid printing every request handled.
    """
    timeout = False

    def log_message(self, format, *args):
        """Avoids printing every request handled."""
        pass

    def do_HEAD(self):
        """Override the do_HEAD method of http.server.SimpleHTTPRequestHandler. It just adds the possibility to timeout."""
        if self.__class__.timeout:
            sleep(10)
        return super(self.__class__, self).do_HEAD()

    @classmethod
    def set_timeout(cls, bool):
        """Switch the value of the timeout class attribute that makes HEAD requests timing out or not."""
        cls.timeout = bool


def main():
    print("\nThis script will create and run HTTP servers on the localhost.")

    handlers = []
    count = 0
    json_file = {'websites': []}

    # The interval times are "desynchronized" to avoid as much as possible simultaneous requests that may lead to
    # ConnectionError.

    port = find_free_port()
    json_file['websites'].append({'name': 'Localhost: random state',
                                  'url': 'http://localhost:{}'.format(port),
                                  'interval': 5})

    # Creating and starting thread containing the server
    thread = Thread(target=start_server, args=(ModifiedHandler, port,))
    thread.setDaemon(True)
    thread.start()

    sleep(1)

    # Writing the JSON file for easy import.
    dir = os.path.dirname(__file__)
    path_to_new_json = os.path.join(dir, './../website_monitoring/file_to_import/random_state_localhost_import.json')

    with open(path_to_new_json, "w") as f:
        f.write(json.dumps(json_file))

    print("\nJSON created at {}.\n".format(path_to_new_json))

    timeouts = []

    while True:
        random_timeout = random()

        if random_timeout > 1 - PROBABILITY_OF_TIMEOUT:
            timeout = True
        else:
            timeout = False

        timeouts.append(timeout)
        ModifiedHandler.set_timeout(timeout)
        print('Timeout for the next 10 seconds: {}'.format(timeout))
        print('Estimated availability for the last 2 min: {:.2f} %'.format(mean(timeouts[-12:]) * 100))
        sleep(10)
        print('\n')


if __name__ == '__main__':
    main()
