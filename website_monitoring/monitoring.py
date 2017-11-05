import requests
from threading import Timer, Lock
import datetime
import pandas as pd
import logging
import os

dir = os.path.dirname(__file__)

logging.basicConfig(
    filename=os.path.join(dir, "./log/events.log"),
    level=logging.INFO,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
)


class WebsiteHandler(object):
    """ Every website entry will have a corresponding WebsiteHandler instance.

    This class will monitor a website using HEAD requests, log the results into a Pandas dataframe, and compute
    statistics and metrics.

    When an instance is created, a timed thread is started to ping the website at periodic intervals.
    """

    # This value is the value for which a website is considered as timing out.
    timeout = 4

    def __init__(self, name, url, interval, parent):
        # Info about the website
        self.name = name
        self.url = url
        self.interval = int(interval)

        self.parent = parent

        # The lock prevent adding an entry to df_history while the statistics are being computed.
        self.lock = Lock()

        self._timer = None  # This attribute will hold the thread
        self.is_running = False
        self.start()

        # This dataframe will hold the historical results of the requests to compute statistics.
        self.df_history = pd.DataFrame()

        self.convert = {"* All": None,
                        "* 2 minutes": datetime.timedelta(minutes=2),
                        "* 10 minutes": datetime.timedelta(minutes=10),
                        "* 1 hour": datetime.timedelta(hours=1),
                        "* 24 hours": datetime.timedelta(days=1)}

        # In case of connection error, no entry is added to df_history.
        # The last connection error is stored in that dict.
        self.connection_error = {'connection error': False,
                                 'name': None,
                                 'details': None,
                                 'last check': None}

        self.on_alert = False
        self.availability = float('nan')
        self.last_header = None
        self.hourly_stats = ['No data', 'No data']

    def has_no_data(self):
        """True if there is no record."""
        return self.df_history.empty

    def _run(self):
        """Thread setup"""
        self.is_running = False
        self.start()
        self.ping_website()

    def start(self):
        """Starts the timed thread."""
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.setDaemon(True)
            self._timer.start()
            self.is_running = True

    def stop(self):
        """Stops the thread."""
        self._timer.cancel()
        self.is_running = False

    def ping_website(self):
        """ This is the method called at regular intervals.

        The method ping the website by performing a HEAD request. I have decided to use a HEAD request rather than a GET
        one to avoid downloading the whole webpage. If an abnormal time is taken during the downloading part, the HEAD
        request won't return a timeout. So the choice between the two is not obvious, but I have decided to stick with the
        HEAD request. I have been testing it with real websites that were down, and it was working well.
        It is easy to modify, just change requests.head to requests.get, and everything will work the same.
        (Change also RunServers.)

        If everything is ok:
         - add to df_history the date, the time elapsed for the request, the status code, and a flag to say it went fine
        If timeout:
         - append a similar line to the dataframe, but with the timeout status and the flag set to False
        If ConnectionError:
         - the df_history dataframe stays the same, and only the connection_error dict is updated.

         At the end of the method, an alert is raised if the availability has gone below 80, or if it has recovered from
         an alert.

        """
        now = datetime.datetime.now()
        try:
            response = requests.head(self.url, timeout=self.__class__.timeout)
        except requests.Timeout:
            self.connection_error['connection error'] = False
            with self.lock:
                self.df_history = self.df_history.append({'date': now,
                                                          'status code': 'Timeout',
                                                          'elapsed': None,
                                                          'OK': False}, ignore_index=True)
        except requests.RequestException as e:
            with self.lock:
                self.connection_error['connection error'] = True
                self.connection_error['name'] = type(e).__name__
                self.connection_error['details'] = type(e).__doc__
                self.connection_error['last check'] = now
                logging.debug('{} -- {}'.format(self.url, e.__doc__))
        else:
            with self.lock:
                self.connection_error['connection error'] = False
                self.df_history = self.df_history.append({'date': now,
                                                          'status code': str(response.status_code),
                                                          'elapsed': response.elapsed,
                                                          'OK': True}, ignore_index=True)

                # Store the last header for the detailed stats.
                self.last_header = response.headers

        # Check for alerts
        if self.on_alert:
            self.recover_alert_check()
        else:
            self.trigger_alert_check()

    def get_info_for_grid(self, small_update):
        """ Compute the metrics for the grid and return the values.

        Returns: All the info to fill the grid:
                ['Website', 'Interval Check', 'Last Check', 'Last Status', 'Last Resp. Time', 'availability (2 min)',
                           'MAX (10 min)', 'AVG (10 min)', 'MAX (1 hour)', 'AVG (1 hour)']
        """

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

                if not small_update:
                    mask_1hour = (self.df_history['date'] > (now - datetime.timedelta(hours=1))) & df_OK

                    info += [self.elapsed_to_string(self.df_history.loc[mask_10min]['elapsed'].max()),
                             self.elapsed_to_string(self.df_history.loc[mask_10min]['elapsed'].mean()),
                             self.elapsed_to_string(self.df_history.loc[mask_1hour]['elapsed'].max()),
                             self.elapsed_to_string(self.df_history.loc[mask_1hour]['elapsed'].mean()),
                             self.availability_to_string(self.availability)]

                    self.hourly_stats = [info[7], info[8]]

                else:
                    info += [self.elapsed_to_string(self.df_history.loc[mask_10min]['elapsed'].max()),
                             self.elapsed_to_string(self.df_history.loc[mask_10min]['elapsed'].mean()),
                             self.hourly_stats[0],
                             self.hourly_stats[1],
                             self.availability_to_string(self.availability)]

        return info

    def availability_to_string(self, availability):
        """Format for the availability fields."""
        # Check if availability == NaN (pandas returns NaN if there was no value to compute the metric)
        if availability == availability:
            return '{:.2f} %'.format(self.availability * 100)
        else:
            return 'No data'

    def elapsed_to_string(self, time_elapsed):
        """Format for time elapsed fields."""
        if time_elapsed == time_elapsed and time_elapsed is not None:
            return '{}.{:03d}s'.format(time_elapsed.seconds, time_elapsed.microseconds // 1000)
        else:
            return 'No data'

    def get_detailed_stats_fixed(self):
        """Return the time independent information about the website for the detailed info frame."""
        return [['Website', self.name], ['URL', self.url], ['Interval', self.interval]]

    def get_detailed_stats_dynamic(self, str_time_scale):
        """Returns the time dependent information about the website for the detailed info frame.

        The string str_time_scale comes from the detailed website info form, and is converted into datetime.timedelta
        using the convert dict.

        """
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
        """Triggers an alert if the website's availability goes below 80% for the last 2 minutes."""
        if not self.has_no_data():
            now = datetime.datetime.now()
            mask = self.df_history['date'] > (now - datetime.timedelta(minutes=2))
            self.availability = self.df_history[mask]['OK'].mean()
            if self.availability < 0.8:
                self.parent.trigger_alert(self.url, self.name, self.availability, now)
                self.on_alert = True

    def recover_alert_check(self):
        """Check if the website has recovered from the previous alert."""
        now = datetime.datetime.now()
        mask = self.df_history['date'] > (now - datetime.timedelta(minutes=2))
        self.availability = self.df_history[mask]['OK'].mean()
        if self.availability > 0.8:
            self.parent.recover_alert(self.url, self.name, self.availability, now)
            self.on_alert = False


class WebsitesContainer(object):
    """The different WebsiteHandlers are stored in a WebsiteContainer instance."""

    def __init__(self):
        self.website_handlers = []
        self.wg_alert_box = None

        # The lock prevents alerts from being written at the same time in the wg_alert_box widget.
        self.lock = Lock()

    def get_website_handler(self, index):
        """Returns the index_th website handler."""
        return self.website_handlers[index]

    def add(self, website):
        """Adds a website to monitor."""
        self.website_handlers.append(WebsiteHandler(*website, self))

    def get_detailed_stats_fixed(self, index):
        """Returns the time independent info of the index_th website."""
        return self.website_handlers[index].get_detailed_stats_fixed()

    def get_detailed_stats_dynamic(self, index, str_time_scale):
        """Returns the time dependent info of the index_th website."""
        return self.website_handlers[index].get_detailed_stats_dynamic(str_time_scale)

    def list_all_websites(self, small_update):
        """Returns the info to fill the grid."""
        grid_info = []
        for website_handler in self.website_handlers:
            grid_info.append(website_handler.get_info_for_grid(small_update=small_update))
        return grid_info

    def stop_all_checks(self):
        """Stops all threads. Called before exiting."""
        for website_handler in self.website_handlers:
            website_handler.stop()

    def set_alert_box(self, wgAlertBox):
        self.wg_alert_box = wgAlertBox

    def trigger_alert(self, url, name, availability, now):
        """Triggers an alert: writes it in the alert box, and logs it."""
        with self.lock:
            assert self.wg_alert_box is not None
            self.wg_alert_box.add_line(
                ["Website {} is down. availability={:.2f}, time={}".format(name, availability,
                                                                           now.strftime('%H:%M:%S.%f')[:-3])])
            logging.info("Website {} is down. availability={:.2f}".format(url, availability,
                                                                          now.strftime('%H:%M:%S.%f')[:-3]))

    def recover_alert(self, url, name, availability, now):
        """Recovers from an alert: writes it in the alert box, and logs it."""
        with self.lock:
            assert self.wg_alert_box is not None
            self.wg_alert_box.add_line(
                ["Website {} recovered. availability={:.2f}, time={}".format(name, availability,
                                                                             now.strftime('%H:%M:%S.%f')[:-3])])
            logging.info("Website {} recovered. availability={:.2f}".format(url, availability,
                                                                            now.strftime('%H:%M:%S.%f')[:-3]))


class GridUpdater(object):
    """This class is used to update the grid."""

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
        full_update = (self.counter % 6 == 0)
        self.wgWebsiteGrid.values = self.main_form.parentApp.websitesContainer.list_all_websites(not full_update)
        self.counter += 1
        if self.main_form.parentApp.getHistory()[-1] == 'MAIN':
            self.wgWebsiteGrid.display()

    def _run(self):
        self.is_running = False
        self.start()
        self.updater()

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.setDaemon(True)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False
