import requests
from threading import Timer


class WebsiteHandler(object):
    timeout = 1

    def __init__(self, name, url, interval):
        self._timer = None
        self.name = name
        self.url = url
        self.interval = interval
        self.is_running = False
        # TODO Maybe not starting directly
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.ping_website()

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

    def ping_website(self):
        # TODO Handle all exceptions possible : status code, no connexion, website does not exist...
        try:
            response = requests.head(self.url, timeout=self.__class__.timeout)
        except TimeoutError:
            return -1, -1
        print(self.name, response.elapsed, response.status_code)
        return response.elapsed, response.status_code


def main():
    from time import sleep

    w1 = WebsiteHandler('Google', 'https://www.google.fr', 2)
    w2 = WebsiteHandler('StackOverFlow', 'https://stackoverflow.com/', 5)

    print("starting...")
    try:
        sleep(50)  # your long-running job goes here...
    finally:
        w1.stop()  # better in a try/finally block to make sure the program ends!
        w2.stop()


if __name__ == '__main__':
    main()
