# -*- coding: utf-8 -*-
import npyscreen
import curses
import requests
import monitoring
import json
import exceptions as err


# WIDGETS

class WebsiteGridWidget(npyscreen.GridColTitles):
    # TODO Annoying thing: to exit the grid you need to press tab. Overwrite h_... to leave the grid when at the end
    # TODO Bug: when right arrow on the empty grid, exception raised. Better init or overwrite the method linked to the right arrow
    def __init__(self, *args, **keywords):
        super(WebsiteGridWidget, self).__init__(*args, **keywords)
        self.default_column_number = 10
        self.col_titles = ['Website', 'Interval Check', 'Last Check', 'Last Status', 'Last Resp. Time',
                           'MAX (10 min)', 'AVG (10 min)', 'MAX (1 hour)', 'AVG (1 hour)', 'Avai. (2 min)']
        # self.values = self.fill_grid()
        self.select_whole_line = True
        self.add_handlers({curses.ascii.NL: self.action_selected})

    def action_selected(self, inpt):
        if self.parent.parentApp.websitesContainer.get(self.edit_cell[0]).has_no_data():
            npyscreen.notify_wait('No data yet, wait a few seconds for the first ping.', 'No data yet')
        else:
            self.parent.parentApp.getForm('WEBSITE_INFO').value = self.edit_cell[0]
            self.parent.parentApp.switchForm('WEBSITE_INFO')

    def custom_print_cell(self, actual_cell, cell_display_value):
        # TODO custom_print_cell
        if len(cell_display_value) > 0 and cell_display_value[-1] == '%':
            availability = int(cell_display_value[:-5])
            if availability <= 80 :
                actual_cell.color = 'DANGER'
            elif availability <= 90:
                actual_cell.color = 'CAUTION'
            else:
                actual_cell.color = 'GOOD'


    def fill_grid(self):
        values = self.parent.parentApp.websitesContainer.list_all_websites()
        return values


class AlertBoxWidget(npyscreen.TitlePager):
    # TODO Bug: Can't go back to the grid once the titlepager has been selected
    def __init__(self, *args, **keywords):
        super(AlertBoxWidget, self).__init__(*args, **keywords)
        self.parent.parentApp.websitesContainer.set_alert_box(self)

    def add_line(self, line):
        """ Add line - line is a list containing the string"""
        self.values = line + self.values
        if self.parent.parentApp.getHistory()[-1] == 'MAIN':
            self.display()


class PickTimeScaleWidget(npyscreen.MultiLine):
    def __init__(self, *args, **keywords):
        super(PickTimeScaleWidget, self).__init__(*args, **keywords)
        self.add_handlers({curses.ascii.NL: self.actionHighlighted})

    def actionHighlighted(self, inpt):
        self.parent.display_info(self.values[self.cursor_line])


# FORMS

class AddWebsiteForm(npyscreen.ActionFormV2):
    # TODO Improve the look (smaller, add line between wg)
    # TODO add the new websites to the grid after adding
    def create(self):
        self.name = "New Website"
        entry_pos = 25
        self.wgName = self.add(npyscreen.TitleText, name="Entry name:", value="", begin_entry_at=entry_pos)
        self.wgAddress = self.add(npyscreen.TitleText, name="Website address:", begin_entry_at=entry_pos)
        self.wgInterval = self.add(npyscreen.TitleText, name="Check interval:", begin_entry_at=entry_pos)

    def beforeEditing(self):
        if self.value is None:
            self.wgName.value = ''
            self.wgAddress.value = ''
            self.wgInterval.value = ''

    def on_ok(self):
        # TODO If confirmed, ask if the user want to check the settings
        # TODO Check if the values seem to be correct (check if int...), check if no empty values
        self.value = True
        try:
            self.checkSettings()
        except err.WhileCheckingException as e:
            npyscreen.notify_confirm(e.__doc__, editw=1)

        else:
            ping_message = """Do you want to first ping the website?
            This will check if the URL given is correct."""
            first_ping = npyscreen.notify_yes_no(ping_message, 'Initial ping', editw=1)
            if first_ping:
                # TODO I dont like doing that here, i need to import requests here just for that. Do it in monitoring
                try:
                    response = requests.head(self.wgAddress.value, timeout=3)
                except requests.Timeout:
                    add_anyway = npyscreen.notify_yes_no("Request timed out. Add the website anyway?", 'Timeout',
                                                         editw=1)
                    # TODO it won't work like that, change this
                    if not add_anyway:
                        return None
                except requests.RequestException as e:
                    npyscreen.notify_confirm(e.__doc__, editw=1)
                    return None
                else:
                    npyscreen.notify_wait(
                        'Status code: {} \n Response time: {}'.format(response.elapsed, response.status_code))
                    self.parentApp.websitesContainer.add(
                        [self.wgName.value, self.wgAddress.value, self.wgInterval.value])
                    npyscreen.notify_confirm('Change saved!', editw=1)
                    self.parentApp.switchForm('MAIN')

    def checkSettings(self):
        if not self.wgName.value:
            raise err.EmptyNameException
        if not self.wgAddress.value:
            raise err.EmptyURLException
        if not self.wgInterval.value:
            raise err.EmptyIntervalException
        try:
            int(self.wgInterval.value)
        except ValueError:
            raise err.BadIntervalException

    def on_cancel(self):
        exiting = npyscreen.notify_yes_no('Are you sure you want to exit without saving?', editw=1)
        if exiting:
            npyscreen.notify('Your changes were NOT saved')
            self.parentApp.switchForm('MAIN')
        else:
            self.value = True


class ImportWebsiteForm(npyscreen.ActionFormV2):
    def create(self):
        self.wgFilenameHolder = self.add(npyscreen.TitleFilenameCombo, name='Choose the file to import',
                                         begin_entry_at=40)

    def import_websites(self):
        # TODO add exceptions
        with open(self.wgFilenameHolder.value) as f:
            json_website = f.read()
        decoded = json.loads(json_website)
        for website in decoded['websites']:
            self.parentApp.websitesContainer.add(list(website.values()))

    def on_ok(self):
        self.import_websites()
        npyscreen.notify('Import done.', 'Import')
        self.parentApp.switchForm('MAIN')

    def on_cancel(self):
        exiting = npyscreen.notify_yes_no('Are you sure you want to exit without importing?', editw=1)
        if exiting:
            npyscreen.notify('The import was NOT done.', 'Import')
            self.parentApp.switchForm('MAIN')
        else:
            pass


class WebsiteInfoForm(npyscreen.Form):
    # TODO Make the last header optional? Might have issues with smaller terminals
    def create(self):
        self.value = None
        self.add(npyscreen.FixedText, value='Pick a time frame', color='WARNING')
        self.wgPickTime = self.add(PickTimeScaleWidget, value=[1, ], max_height=6,
                                   values=["* All", "* 1 minute", "* 10 minutes", "* 1 hour", "* 24 hours"],
                                   rely=4, relx=10)

        self.add(npyscreen.FixedText, value='Global info', rely=10, color='DANGER')

        self.wgFixedInfoGrid = self.add(npyscreen.SimpleGrid, relx=3, rely=12, default_column_number=2, max_height=3)

        self.wgSubtitle = self.add(npyscreen.FixedText, rely=16, color='DANGER')

        self.add(npyscreen.FixedText, value='* Availability', relx=4, rely=18, color='WARNING')
        self.wgAvailability = self.add(npyscreen.FixedText, relx=12, rely=20)

        self.add(npyscreen.FixedText, value='* Response time', relx=4, rely=22, color='WARNING')
        self.wgResponseGrid = self.add(npyscreen.SimpleGrid, relx=7, rely=24, default_column_number=2, max_height=3)

        self.add(npyscreen.FixedText, value='* Status count', relx=4, rely=28, color='WARNING')
        self.wgStatusGrid = self.add(npyscreen.SimpleGrid, relx=7, rely=30, default_column_number=2, max_height=4)

        self.add(npyscreen.FixedText, value='* Last header', relx=4, rely=35, color='WARNING')
        self.wgHeaderGrid = self.add(npyscreen.SimpleGrid, relx=7, rely=37, default_column_number=2, max_height=10)

    def display_info(self, timescale):
        availability, status_info, response_info, last_header = self.parentApp.websitesContainer.get_detailed_stats_dynamic(
            self.value, timescale)

        self.wgSubtitle.value = 'Info with time frame: ' + timescale[2:]
        self.wgStatusGrid.values = status_info
        self.wgAvailability.value = '{:.2f} %'.format(availability * 100)
        self.wgResponseGrid.values = response_info
        self.wgHeaderGrid.values = last_header
        # self.wgHeaderGrid.values = [[1,2], [3,4]]

        self.wgStatusGrid.display()
        self.wgSubtitle.display()
        self.wgAvailability.display()
        self.wgResponseGrid.display()
        self.wgHeaderGrid.display()

    def beforeEditing(self):
        self.clear()
        self.name = "Website " + self.parentApp.websitesContainer.get(self.value).name
        self.wgSubtitle.value = 'Info with time frame: Nothing selected'
        self.wgFixedInfoGrid.values = self.parentApp.websitesContainer.get_detailed_stats_fixed(self.value)

    def clear(self):
        self.wgStatusGrid.values = []
        self.wgResponseGrid.values = []
        self.wgAvailability.value = ''
        self.wgHeaderGrid.values = []

    def afterEditing(self):
        self.parentApp.switchForm('MAIN')


class MainForm(npyscreen.FormWithMenus, npyscreen.ActionFormMinimal):
    GRID_UPDATE_FREQ = 5

    # TODO Change the label of the OK button for something like EXIT if possible
    # TODO Add a widget on top to tell when was opened the app?
    # TODO Dynamic partitioning between the grid and the alert box

    def create(self):
        self.wgWebsiteGrid = self.add(WebsiteGridWidget, name='Monitoring', max_height=25)
        # TODO Don't hard code rely, otherwise app can't open if terminal not big enough.
        self.wgAlertBox = self.add(AlertBoxWidget, name='Alerts', rely=-10)

        self.main_menu = self.new_menu(name='Main menu')

        self.main_menu.addItem('Add new website', self.get_form_add_website, shortcut='a')
        self.main_menu.addItem('Import list of website', self.get_form_import_list_website, shortcut='i')

        self.grid_updater = monitoring.GridUpdater(self.__class__.GRID_UPDATE_FREQ, self.wgWebsiteGrid, self)

    def get_form_add_website(self):
        self.parentApp.getForm('ADD_WEBSITE').value = None
        self.parentApp.switchForm('ADD_WEBSITE')

    def get_form_import_list_website(self):
        self.parentApp.getForm('IMPORT_WEBSITE').value = None
        self.parentApp.switchForm('IMPORT_WEBSITE')

    def beforeEditing(self):
        pass
        # self.wgWebsiteGrid.values = self.parentApp.websitesContainer.list_all_websites()
        # self.wgWebsiteGrid.display()

    def on_ok(self):
        # This button will stop the app.
        # Stopping the threads:
        self.parentApp.websitesContainer.stop_all_checks()
        self.grid_updater.stop()

        self.parentApp.switchForm(None)


# APP

class WebsiteMonitoringApplication(npyscreen.NPSAppManaged):
    def onStart(self):
        self.websitesContainer = monitoring.WebsitesContainer()
        self.addForm('MAIN', MainForm)
        self.addForm('ADD_WEBSITE', AddWebsiteForm)
        self.addForm('WEBSITE_INFO', WebsiteInfoForm)
        self.addForm('IMPORT_WEBSITE', ImportWebsiteForm)

# TODO add timeout as arg

if __name__ == '__main__':
    app = WebsiteMonitoringApplication()
    app.run()
