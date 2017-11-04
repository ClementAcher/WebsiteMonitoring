# -*- coding: utf-8 -*-
import npyscreen
import curses
import requests
import monitoring
import json
import exceptions as err


# TODO add logging

# WIDGETS

class WebsiteGridWidget(npyscreen.GridColTitles):
    def __init__(self, *args, **keywords):
        super(WebsiteGridWidget, self).__init__(*args, **keywords)

        self.default_column_number = 10
        self.col_titles = ['Website',
                           'Interval Check',
                           'Last Check',
                           'Last Status',
                           'Last Resp. Time',
                           'MAX (10 min)',
                           'AVG (10 min)',
                           'MAX (1 hour)',
                           'AVG (1 hour)',
                           'Avai. (2 min)']

        self.select_whole_line = True

        # Add the possibility to get more info on a website by selecting it
        self.add_handlers({curses.ascii.NL: self.action_selected})

        # Npyscreen doesn't handle right an empty grid. Overriding of the handlers needed.
        self.handlers[curses.KEY_RIGHT] = self.h_move_cell_right_mod
        self.handlers[curses.KEY_DOWN] = self.h_move_cell_down_mod

    def action_selected(self, inpt):
        """Open a frame with more info on the website."""
        if self.parent.parentApp.websitesContainer.get(self.edit_cell[0]).has_no_data():
            npyscreen.notify_wait('No data yet, wait for the first ping.', 'No data yet')
        else:
            self.parent.parentApp.getForm('WEBSITE_INFO').value = self.edit_cell[0]
            self.parent.parentApp.switchForm('WEBSITE_INFO')

    def custom_print_cell(self, actual_cell, cell_display_value):
        """Custom printing of the cells: adding colors."""
        # TODO Got an exception here with ValueError: better do this
        if cell_display_value == 'Timeout':
            actual_cell.color = 'DANGER'
        elif len(cell_display_value) > 0 and cell_display_value[-1] == '%':
            try:
                availability = int(cell_display_value[:-5])
                if availability <= 80:
                    actual_cell.color = 'DANGER'
                elif availability <= 90:
                    actual_cell.color = 'CAUTION'
                else:
                    actual_cell.color = 'GOOD'
            except ValueError:
                # This should not happen
                pass
        else:
            actual_cell.color = 'WHITE'

    def h_move_cell_right_mod(self, inpt):
        """Right key callback: handling empty grid exception."""
        try:
            if self.values is not None:
                self.h_move_cell_right(inpt)
        except IndexError:
            pass

    def h_move_cell_down_mod(self, inpt):
        """Down key callback: handling empty grid exception."""
        try:
            if self.values is not None:
                self.h_move_line_down(inpt)
        except IndexError:
            pass


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
        self.value = True
        try:
            self.checkSettings()
        except err.WhileCheckingException as e:
            npyscreen.notify_confirm(e.__doc__, editw=1)

        else:
            ping_message = """The script is going to perform a first ping to check if the URL is correct."""
            npyscreen.notify_confirm(ping_message, 'Checking the URL', editw=1)
            # TODO I dont like doing that here, i need to import requests here just for that. Do it in monitoring
            try:
                response = requests.head(self.wgAddress.value, timeout=5)
            except requests.Timeout:
                add_anyway = npyscreen.notify_yes_no("Request timed out. Add the website anyway?", 'Timeout',
                                                     editw=1)
                if not add_anyway:
                    return None
            except requests.RequestException as e:
                npyscreen.notify_confirm(e.__doc__, editw=1)
                return None
            else:
                npyscreen.notify_confirm(
                    '\n\nStatus code: {} \nResponse time: {}'.format(response.status_code, response.elapsed), editw=1)
            self.parentApp.websitesContainer.add([self.wgName.value, self.wgAddress.value, self.wgInterval.value])
            npyscreen.notify_confirm('Changes saved!', editw=1)

            self.parentApp.getForm('MAIN').update_grid_on_display = True
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
        if int(self.wgInterval.value) == 0:
            raise err.TooSmallIntervalException

    def on_cancel(self):
        exiting = npyscreen.notify_yes_no('Are you sure you want to exit without saving?', editw=1)
        if exiting:
            npyscreen.notify('Your changes were NOT saved')
            self.parentApp.switchForm('MAIN')
        else:
            self.value = True


class ImportWebsiteForm(npyscreen.ActionFormV2):
    """ Form to import websites from a JSON file.

    Allows the user to select a JSON file containing websites to add. The format can be found in the sample JSON
    available on the repo.
    Note that the websites won't be pinged to check the URL during the import for efficiency reasons.
    Importing valid websites is a task left to the user.

    """

    def create(self):
        """Create is called in the constructor of the form. Adds the widgets to the form."""

        self.wgFilenameHolder = self.add(npyscreen.TitleFilenameCombo,
                                         name='Choose a JSON file to import',
                                         begin_entry_at=40)

    def import_websites(self):
        """
        Imports website from the selected file.
        Exception raised if no file has been selected, or the library json could not parse the file.
        No other checks are done.
        """
        if self.wgFilenameHolder.value is None:
            raise err.NoFileSelectedException
        with open(self.wgFilenameHolder.value) as f:
            json_website = f.read()
        decoded = json.loads(json_website)

        for website in decoded['websites']:
            self.parentApp.websitesContainer.add(list(website.values()))

    def on_ok(self):
        try:
            self.import_websites()
        except err.NoFileSelectedException:
            npyscreen.notify_confirm(err.NoFileSelectedException.__doc__, 'Import error',
                                     editw=1)
        except json.JSONDecodeError:
            npyscreen.notify_confirm('Cannot decode the file. Are you sure this is a JSON file?', 'Import error',
                                     editw=1)
        else:
            npyscreen.notify('Import done.', 'Import')

            self.parentApp.getForm('MAIN').update_grid_on_display = True
            self.parentApp.switchForm('MAIN')

    def on_cancel(self):
        exiting = npyscreen.notify_yes_no('Are you sure you want to exit without importing?', editw=1)
        if exiting:
            npyscreen.notify('The import was NOT done.', 'Import')
            self.parentApp.switchForm('MAIN')
        else:
            pass


class WebsiteInfoForm(npyscreen.Form):
    """ Form giving detailed info about a specific website

    The user can access from the MAIN_FORM by selecting an entry in the grid.
    It gives, for a user-defined time frame, detailed stats about the website. Info about:
      - Availability
      - Response time
      - Status count
      - Last header

    """

    def create(self):
        self.value = None

        # Timeframe selector
        self.add(npyscreen.FixedText, value='Pick a time frame', color='WARNING', editable=False)
        self.wgPickTime = self.add(PickTimeScaleWidget, value=[1, ], max_height=6,
                                   values=["* All", "* 1 minute", "* 10 minutes", "* 1 hour", "* 24 hours"],
                                   rely=4, relx=10, scroll_exit=True)

        # Global info
        self.add(npyscreen.FixedText, value='Global info', rely=10, color='DANGER', editable=False)
        self.wgFixedInfoGrid = self.add(npyscreen.SimpleGrid, relx=3, rely=12, default_column_number=2, max_height=3,
                                        editable=False)

        # Info linked to the chosen frame
        self.wgSubtitle = self.add(npyscreen.FixedText, rely=16, color='DANGER', editable=False)

        self.add(npyscreen.FixedText, value='* Availability', relx=4, rely=18, color='WARNING', editable=False)
        self.wgAvailability = self.add(npyscreen.FixedText, relx=12, rely=20, editable=False)

        self.add(npyscreen.FixedText, value='* Response time', relx=4, rely=22, color='WARNING', editable=False)
        self.wgResponseGrid = self.add(npyscreen.SimpleGrid, relx=7, rely=24, default_column_number=2, max_height=3,
                                       editable=False)

        self.add(npyscreen.FixedText, value='* Status count', relx=4, rely=28, color='WARNING', editable=False)
        self.wgStatusGrid = self.add(npyscreen.SimpleGrid, relx=7, rely=30, default_column_number=2, max_height=4,
                                     editable=False)

        self.add(npyscreen.FixedText, value='* Last header', relx=4, rely=35, color='WARNING', editable=False)
        self.wgHeaderGrid = self.add(npyscreen.SimpleGrid, relx=7, rely=37, default_column_number=2, max_height=10,
                                     editable=False)

    def display_info(self, timescale):
        availability, status_info, response_info, last_header = self.parentApp.websitesContainer.get_detailed_stats_dynamic(
            self.value, timescale)

        self.wgSubtitle.value = 'Info with time frame: ' + timescale[2:]
        self.wgStatusGrid.values = status_info
        self.wgAvailability.value = availability
        self.wgResponseGrid.values = response_info
        self.wgHeaderGrid.values = last_header

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
    """ Main form

    It contains the grid with all the websites that have been added, and a box logging
    all the down/recovered notifications.
    From that form, it possible to access to other forms to import/add more websites through a menu.

     """

    GRID_UPDATE_FREQ = 5

    # TODO Change the label of the OK button for something like EXIT if possible
    # TODO Add a widget on top to tell when was opened the app?
    # TODO Dynamic partitioning between the grid and the alert box

    def create(self):
        """Create is called in the constructor of the form. Adds all the widgets and handlers and creates the menu."""

        self.help = "Test"
        self.wgWebsiteGrid = self.add(WebsiteGridWidget, name='Monitoring', max_height=25, rely=3)
        # TODO Don't hard code rely, otherwise app can't open if terminal not big enough.
        self.wgAlertBox = self.add(AlertBoxWidget, name='Alerts', rely=-10)

        self.main_menu = self.new_menu(name='Main menu')

        self.main_menu.addItem('Add new website', self.get_form_add_website, shortcut='a')
        self.main_menu.addItem('Import list of website', self.get_form_import_list_website, shortcut='i')

        self.grid_updater = monitoring.GridUpdater(self.__class__.GRID_UPDATE_FREQ, self.wgWebsiteGrid, self)

        self.update_grid_on_display = False

        self.add_handlers({'t': self.h_selectGrid})
        self.add_handlers({'p': self.print_highlighted})

    # TODO Not really good workaround...
    def h_selectGrid(self, inpt):
        """Callback to select the grid."""
        if self.editw != 0:
            self.wgAlertBox.add_line(['edit'])
            npyscreen.ActionFormMinimal.edit(self)

    def print_highlighted(self, inpt):
        self.wgAlertBox.add_line([self.editw])

    def get_form_add_website(self):
        """Method called from the menu: display the ADD_WEBSITE form."""
        self.parentApp.getForm('ADD_WEBSITE').value = None
        self.parentApp.switchForm('ADD_WEBSITE')

    def get_form_import_list_website(self):
        """Method called from the menu: display the ADD_WEBSITE form."""
        self.parentApp.getForm('IMPORT_WEBSITE').value = None
        self.parentApp.switchForm('IMPORT_WEBSITE')

    def beforeEditing(self):
        """
        Method called before the form is displayed (for instance, when the user switch from another to this one).
        update_grid_on_display is a boolean to update the grid only if at least one website has been added to the grid.
        """
        if self.update_grid_on_display:
            self.update_grid()
            self.update_grid_on_display = False

    def on_ok(self):
        """"Called when the OK button is selected. Closes the app, and stop all the running threads."""
        self.parentApp.websitesContainer.stop_all_checks()
        self.grid_updater.stop()

        self.parentApp.switchForm(None)

    def update_grid(self):
        """Update the grid widget."""
        self.wgWebsiteGrid.values = self.parentApp.websitesContainer.list_all_websites()
        self.wgWebsiteGrid.display()

# APPLICATION

class WebsiteMonitoringApplication(npyscreen.NPSAppManaged):
    """Application

    The application is the object managing all the forms.
    The Npyscreen logic is : application > forms > widgets.
    """
    def onStart(self):
        """
        Method called when the app is started through the .run method in the main.
        Adds all the form to the application.
        """
        self.websitesContainer = monitoring.WebsitesContainer()
        self.addForm('MAIN', MainForm)
        self.addForm('ADD_WEBSITE', AddWebsiteForm)
        self.addForm('WEBSITE_INFO', WebsiteInfoForm)
        self.addForm('IMPORT_WEBSITE', ImportWebsiteForm)


# TODO add timeout as arg

if __name__ == '__main__':
    app = WebsiteMonitoringApplication()
    app.run()
