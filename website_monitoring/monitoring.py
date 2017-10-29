import requests
from threading import Timer
import datetime
import pandas as pd


class WebsiteHandler(object):
    # TODO Better define this
    timeout = 2

    # TODO Implement the final data structure to store the different metrics
    def __init__(self, name, url, interval):
        self._timer = None
        self.name = name
        self.url = url
        self.interval = int(interval)
        self.is_running = False
        # TODO Maybe not starting directly
        self.start()

        # TODO See if it is possible to force de type for the columns
        self.df_history = pd.DataFrame()

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
        # TODO Handle all exceptions possible : status code, no connexion, website does not exist... See requests doc
        now = datetime.datetime.now()
        try:
            response = requests.head(self.url, timeout=self.__class__.timeout)
        # TODO ReadTimeout instead
        except requests.ReadTimeout:
            self.df_history = self.df_history.append({'date': now,
                                                      'status code': 'Timeout',
                                                      'elapsed': datetime.timedelta(0),
                                                      'OK': False}, ignore_index=True)
        else:
            self.df_history = self.df_history.append({'date': now,
                                                      'status code': int(response.status_code),
                                                      'elapsed': response.elapsed,
                                                      'OK': True}, ignore_index=True)
            # return response.elapsed, response.status_code

    def get_info_for_grid(self):

        # ['Website', 'Interval Check', 'Last Check', 'Last Status', 'Last Resp. Time',
        #                    'MAX (10 min)', 'AVG (10 min)', 'MAX (1 hour)', 'AVG (1 hour)']

        info = [self.name, self.interval]
        if self.df_history.empty:
            info += [None] * 7
        else:
            # TODO clean that, a little bit messy
            tail = self.df_history.tail(n=1).values
            info += [tail[0, 1].strftime('%H:%M:%S.%f')[:-3],  # Last check
                     tail[0, 3],  # Last status
                     tail[0, 2].microseconds / 1000]  # Last Resp. Time

            df_OK = self.df_history['OK'] == 1
            mask_2min = (self.df_history['date'] > (datetime.datetime.now() - datetime.timedelta(minutes=10))) & df_OK
            mask_1hour = (self.df_history['date'] > (datetime.datetime.now() - datetime.timedelta(hours=1))) & df_OK

            # TODO Exceptions if empty

            info += [str(self.df_history.loc[mask_2min]['elapsed'].max().microseconds / 1000),
                     str(self.df_history.loc[mask_2min]['elapsed'].mean().microseconds / 1000),
                     str(self.df_history.loc[mask_1hour]['elapsed'].max().microseconds / 1000),
                     str(self.df_history.loc[mask_1hour]['elapsed'].mean().microseconds / 1000)]

        return info

    def get_detailed_stats(self):
        return [self.name, self.url, self.interval, str(self.last_elapsed), str(self.last_time_checked)]


class WebsitesContainer(object):
    def __init__(self):
        self.website_handlers = []

    def add(self, website):
        self.website_handlers.append(WebsiteHandler(*website))

    def get_detailed_stats(self, index):
        return self.website_handlers[index].get_detailed_stats()

    def list_all_websites(self):
        grid_info = []
        for website_handler in self.website_handlers:
            grid_info.append(website_handler.get_info_for_grid())
        return grid_info

    def stop_all_checks(self):
        for website_handler in self.website_handlers:
            website_handler.stop()


class GridUpdater(object):
    def __init__(self, interval, wgWebsiteGrid, main_form):
        self._timer = None
        self.interval = interval
        self.wgWebsiteGrid = wgWebsiteGrid
        self.main_form = main_form
        self.is_running = False
        # Keep track for updates on a different timescale
        self.counter = 0
        self.start()

    def updater(self):
        self.wgWebsiteGrid.values = self.main_form.parentApp.websitesContainer.list_all_websites()
        self.counter += 1
        # TODO : update different things when self.counter % x == 0
        if self.main_form.parentApp.getHistory()[-1] == 'MAIN':
            self.wgWebsiteGrid.display()

    def _run(self):
        self.is_running = False
        self.start()
        self.updater()

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

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
