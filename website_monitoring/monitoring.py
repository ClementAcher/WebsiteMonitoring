import requests
from threading import Timer, Lock
import datetime
import pandas as pd
import logging

logging.basicConfig(
    filename="./log/events.log",
    level=logging.INFO,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
)


class WebsiteHandler(object):
    # TODO Better define this
    timeout = 2

    def __init__(self, name, url, interval, parent):
        self._timer = None
        self.name = name
        self.url = url
        self.interval = int(interval)
        self.parent = parent
        self.lock = Lock()
        self.is_running = False
        self.start()

        self.df_history = pd.DataFrame()

        self.convert = {"* All": None,
                        "* 1 minute": datetime.timedelta(minutes=1),
                        "* 10 minutes": datetime.timedelta(minutes=10),
                        "* 1 hour": datetime.timedelta(hours=1),
                        "* 24 hours": datetime.timedelta(days=1)}

        self.connection_error = {'connection error': False,
                                 'name': None,
                                 'details': None,
                                 'last check': None}

        self.on_alert = False
        self.availability = float('nan')
        self.last_header = None

    def has_no_data(self):
        return self.df_history.empty

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
        with self.lock:
            now = datetime.datetime.now()
            try:
                response = requests.head(self.url, timeout=self.__class__.timeout)
            except requests.Timeout:
                self.connection_error['connection error'] = False
                self.df_history = self.df_history.append({'date': now,
                                                          'status code': 'Timeout',
                                                          'elapsed': None,
                                                          'OK': False}, ignore_index=True)
            except requests.ConnectionError as e:
                self.connection_error['connection error'] = True
                self.connection_error['name'] = e.__class__.__name__
                self.connection_error['details'] = e.__doc__
                self.connection_error['last check'] = now
                logging.debug('{} -- {}'.format(self.url, e.__doc__))
            else:
                self.connection_error['connection error'] = False
                self.df_history = self.df_history.append({'date': now,
                                                          'status code': str(response.status_code),
                                                          'elapsed': response.elapsed,
                                                          'OK': True}, ignore_index=True)

                self.last_header = response.headers

            if self.on_alert:
                self.recover_alert_check()
            else:
                self.trigger_alert_check()

    def get_info_for_grid(self):

        # ['Website', 'Interval Check', 'Last Check', 'Last Status', 'Last Resp. Time', 'availability (2 min)',
        #                    'MAX (10 min)', 'AVG (10 min)', 'MAX (1 hour)', 'AVG (1 hour)']

        info = [self.name, self.interval]

        with self.lock:
            if self.has_no_data():
                if self.connection_error['connection error']:
                    info += [self.connection_error['last check'].strftime('%H:%M:%S.%f')[:-3],  # Last check
                             self.connection_error['name']]  # Last status
                    info += [None] * 6
                else:
                    info += [None] * 8
            else:
                # TODO clean that, a little bit messy
                tail = self.df_history.tail(n=1).values
                if not self.connection_error['connection error']:
                    info += [tail[0, 1].strftime('%H:%M:%S.%f')[:-3],  # Last check
                             tail[0, 3],  # Last status
                             self.elapsed_to_string(tail[0, 2])]  # Last Resp. Time
                else:
                    info += [self.connection_error['last check'].strftime('%H:%M:%S.%f')[:-3],  # Last check
                             self.connection_error['name'],  # Last status
                             None]  # Last Resp. Time

                df_OK = self.df_history['OK'] == 1
                now = datetime.datetime.now()
                mask_10min = (self.df_history['date'] > (now - datetime.timedelta(minutes=10))) & df_OK
                mask_1hour = (self.df_history['date'] > (now - datetime.timedelta(hours=1))) & df_OK

                info += [self.elapsed_to_string(self.df_history.loc[mask_10min]['elapsed'].max()),
                         self.elapsed_to_string(self.df_history.loc[mask_10min]['elapsed'].mean()),
                         self.elapsed_to_string(self.df_history.loc[mask_1hour]['elapsed'].max()),
                         self.elapsed_to_string(self.df_history.loc[mask_1hour]['elapsed'].mean()),
                         self.availability_to_string(self.availability)]

        return info

    def availability_to_string(self, availability):
        if availability == availability:
            return '{:.2f} %'.format(self.availability * 100)
        else:
            return 'No data'

    def elapsed_to_string(self, time_elapsed):
        if time_elapsed == time_elapsed and time_elapsed is not None:
            return '{}.{:03d}s'.format(time_elapsed.seconds, time_elapsed.microseconds // 1000)
        else:
            return 'No data'

    def get_detailed_stats_fixed(self):
        return [['Website', self.name], ['URL', self.url], ['Interval', self.interval]]

    def get_detailed_stats_dynamic(self, str_time_scale):
        # TODO Not empty, but only timeout
        # last_header = [[key, value] for key, value in self.last_header.items()] AttributeError: 'NoneType'
        # object has not attribute 'items'
        converted = self.convert[str_time_scale]
        assert not self.has_no_data()
        with self.lock:
            if converted is None:
                status = self.df_history.groupby(by=['status code']).size().index.tolist()
                counts = self.df_history.groupby(by=['status code']).size().tolist()
                availability = self.availability_to_string(self.df_history['OK'].mean())
                mini = self.df_history.loc[self.df_history['OK'] == 1]['elapsed'].min()
                avg = self.df_history.loc[self.df_history['OK'] == 1]['elapsed'].mean()
                maxi = self.df_history.loc[self.df_history['OK'] == 1]['elapsed'].max()
            else:
                mask = self.df_history['date'] > (datetime.datetime.now() - converted)
                status = self.df_history.loc[mask].groupby(by=['status code']).size().index.tolist()
                counts = self.df_history.loc[mask].groupby(by=['status code']).size().tolist()
                availability = self.availability_to_string(self.df_history.loc[mask]['OK'].mean())
                mini = self.df_history.loc[mask & self.df_history['OK'] == 1]['elapsed'].min()
                avg = self.df_history.loc[mask & self.df_history['OK'] == 1]['elapsed'].mean()
                maxi = self.df_history.loc[mask & self.df_history['OK'] == 1]['elapsed'].max()

            elapsed_info = [[text, self.elapsed_to_string(time)] for text, time in
                            zip(['Min', 'Average', 'Max'], [mini, avg, maxi])]
            status_info = [[stat, count] for stat, count in zip(status, counts)]

            if self.last_header is not None:
                last_header = [[key, value] for key, value in self.last_header.items()]
            else:
                last_header = [['No header']]

        return availability, status_info, elapsed_info, last_header

    def trigger_alert_check(self):
        if not self.has_no_data():
            now = datetime.datetime.now()
            mask = self.df_history['date'] > (now - datetime.timedelta(minutes=2))
            self.availability = self.df_history[mask]['OK'].mean()
            if self.availability < 0.8:
                self.parent.trigger_alert(self.url, self.name, self.availability, now)
                self.on_alert = True

    def recover_alert_check(self):
        now = datetime.datetime.now()
        mask = self.df_history['date'] > (now - datetime.timedelta(minutes=2))
        self.availability = self.df_history[mask]['OK'].mean()
        if self.availability > 0.8:
            self.parent.recover_alert(self.url, self.name, self.availability, now)
            self.on_alert = False


class WebsitesContainer(object):
    def __init__(self):
        self.website_handlers = []
        self.alert_box = None
        self.lock = Lock()

    def get_website_handler(self, index):
        return self.website_handlers[index]

    def add(self, website):
        self.website_handlers.append(WebsiteHandler(*website, self))

    def get_detailed_stats_fixed(self, index):
        return self.website_handlers[index].get_detailed_stats_fixed()

    def get_detailed_stats_dynamic(self, index, str_time_scale):
        return self.website_handlers[index].get_detailed_stats_dynamic(str_time_scale)

    def list_all_websites(self):
        grid_info = []
        for website_handler in self.website_handlers:
            grid_info.append(website_handler.get_info_for_grid())
        return grid_info

    def stop_all_checks(self):
        for website_handler in self.website_handlers:
            website_handler.stop()

    def set_alert_box(self, wgAlertBox):
        self.alert_box = wgAlertBox

    def trigger_alert(self, url, name, availability, now):
        with self.lock:
            assert self.alert_box is not None
            self.alert_box.add_line(
                ["Website {} is down. availability={:.2f}, time={}".format(name, availability,
                                                                           now.strftime('%H:%M:%S.%f')[:-3])])
            logging.info("Website {} is down. availability={:.2f}".format(url, availability,
                                                                          now.strftime('%H:%M:%S.%f')[:-3]))

    def recover_alert(self, url, name, availability, now):
        with self.lock:
            assert self.alert_box is not None
            self.alert_box.add_line(
                ["Website {} recovered. availability={:.2f}, time={}".format(name, availability,
                                                                             now.strftime('%H:%M:%S.%f')[:-3])])
            logging.info("Website {} recovered. availability={:.2f}".format(url, availability,
                                                                            now.strftime('%H:%M:%S.%f')[:-3]))


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
