import http.server
import socketserver
import os
from time import sleep
from threading import Thread
import socket
from contextlib import closing
import json

# This script will create and run a number chosen by the user of servers on the localhost that can be controlled.
# The created servers can easily be set as running normally or as "fake" down server.
# A file to quickly import the servers is created in the WebsiteMonitoring/website_monitoring/file_to_import folder.

# Important note: the number of servers that can be created is limited to 5 because too many servers running at the
# same time led to "ConnectionError" while handling certain requests. Even with a mximum of 5 servers running at the
# same time, it might still happen from time to time. It is also the reason why the interval check time are
# "desynchronised" to avoid several requests to the localhost at the same time.
# This issue has nothing to do with the WebsiteMonitoring app, and might be solved by making the created servers even
# simpler.


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

    def log_message(self, format, *args):
        """Avoids printing every request handled."""
        pass


# The two following methods will be added to the metaclasses created for the different servers/threads.
# Metaclass is the way I found to have the possibility to set the status (timing out/not timing out) of the
# different servers created independently. When a server is running, it will create an Handler instance
# (see start_server) for every request received. The only way then to control the properties of those dynamically
# created instances is to control the class itself, that is why a Handler class is dynamically created for every
# server created.

# Note: I override do_HEAD because the WebsiteMonitoring app does HEAD requests. If it were changed to GET, the
# do_GET method would need to be overridden.

def do_HEAD(self):
    """Override the do_HEAD method of http.server.SimpleHTTPRequestHandler. It just adds the possibility to timeout."""
    if self.__class__.timeout:
        sleep(10)
    return super(self.__class__, self).do_HEAD()


@classmethod
def change_timeout(cls):
    """Switch the value of the timeout class attribute that makes HEAD requests timing out or not."""
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

    # The interval times are "desynchronized" to avoid as much as possible simultaneous requests that may lead to
    # ConnectionError.
    interval_time_list = [3, 7, 4, 9, 10]

    for i in range(n_servers):
        port = find_free_port()
        json_file['websites'].append({'name': 'Localhost {}'.format(i),
                                      'url': 'http://localhost:{}'.format(port),
                                      'interval': interval_time_list[i]})
        # Creating the class
        handlers.append(type('ModifiedHandler_{}'.format(count), (ModifiedHandler,), {'count': count,
                                                                                      'timeout': False,
                                                                                      'do_HEAD': do_HEAD,
                                                                                      'change_timeout': change_timeout}))

        # Creating and starting thread containing the server
        thread = Thread(target=start_server, args=(handlers[-1], port,))
        thread.setDaemon(True)
        thread.start()

        count += 1
        sleep(1)

    # Writing the JSON file for easy import.
    dir = os.path.dirname(__file__)
    path_to_new_json = os.path.join(dir, './../website_monitoring/file_to_import/localhost_import.json')

    with open(path_to_new_json, "w") as f:
        f.write(json.dumps(json_file))

    print("\nJSON created at {}.\n".format(path_to_new_json))

    while True:
        print('CURRENT STATE\n')
        for i, handler in enumerate(handlers):
            print("\t * Server {} -- Timeout: {}".format(i, handler.timeout))

        print("\nType the number of the server to change its status. CTRL+C to quit.")
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
