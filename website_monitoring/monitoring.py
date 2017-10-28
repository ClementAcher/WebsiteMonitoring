import requests
from threading import Timer


class WebsiteHandler(object):
    # TODO Do two different methods: one for the grid, one for the "more info" part
    timeout = 1

    def __init__(self, name, url, interval):
        self._timer = None
        self.name = name
        self.url = url
        self.interval = int(interval)
        self.is_running = False
        # TODO Maybe not starting directly
        self.start()
    #     TODO change the following
        self.last_elapsed = None

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
        """Return info from the header of the website"""
        # TODO Handle all exceptions possible : status code, no connexion, website does not exist...
        # TODO accurate docstring
        try:
            response = requests.head(self.url, timeout=self.__class__.timeout)
        except TimeoutError:
            return -1, -1
        self.last_elapsed = response.elapsed
        return response.elapsed, response.status_code

    def get_info_for_grid(self):
        return [self.name, self.url, self.interval, str(self.last_elapsed)]

    def get_detailed_stats(self):
        return [self.name, self.url, self.interval, str(self.last_elapsed)]

class WebsitesContainer(object):
    def __init__(self):
        self.websites = []

    def add(self, website):
        self.websites.append(WebsiteHandler(*website))

    def get_detailed_stats(self, index):
        return self.websites[index].get_detailed_stats()

    def list_all_websites(self):
        grid_info = []
        for website in self.websites:
            grid_info.append(website.get_info_for_grid())
        return grid_info

# def main():
#     from time import sleep
#
#     w1 = WebsiteHandler('Google', 'https://www.google.fr', 2)
#     w2 = WebsiteHandler('StackOverFlow', 'https://stackoverflow.com/', 5)
#
#     print("starting...")
#     try:
#         sleep(50)
#     finally:
#         w1.stop()
#         w2.stop()


# if __name__ == '__main__':
#     main()
