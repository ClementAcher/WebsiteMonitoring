# -*- coding: utf-8 -*-
import npyscreen
import monitoring
import json


# TODO To handle the update of the grid: only one thread, and check if only one or 2 columns updated

# WIDGETS

class WebsiteGridWidget(npyscreen.GridColTitles):
    # TODO Annoying thing: to exit the grid you need to press tab. Overwrite h_... to leave the grid when at the end
    def __init__(self, *args, **keywords):
        super(WebsiteGridWidget, self).__init__(*args, **keywords)
        # TODO Implement the final grid
        self.default_column_number = 5
        self.col_titles = ['Website', 'Interval Check', 'Status']
        self.values = self.fill_grid()
        self.select_whole_line = True
        self.handlers["^O"] = self.action_selected

    def action_selected(self, inpt):
        self.parent.parentApp.getForm('WEBSITE_INFO').value = self.edit_cell[0]
        self.parent.parentApp.switchForm('WEBSITE_INFO')

    def custom_print_cell(self, actual_cell, cell_display_value):
        # TODO custom_print_cell
        pass

    def fill_grid(self):
        values = self.parent.parentApp.websitesContainer.list_all_websites()
        return values


class AlertBoxWidget(npyscreen.TitlePager):
    def __init__(self, *args, **keywords):
        super(AlertBoxWidget, self).__init__(*args, **keywords)
        self.values = [["""{} Website website is down. availability=availablility, time=time""".format(i)] for i
                       in range(100)]

    def add_line(self, line):
        """ Add line - line is a list containing the string"""
        self.values = line + self.values


# FORMS

class AddWebsiteForm(npyscreen.ActionFormV2):
    # TODO Improve the look (smaller, add line between wg)
    def create(self):
        self.name = "New Website"
        entry_pos = 25
        self.wgName = self.add(npyscreen.TitleText, name="Entry name:", begin_entry_at=entry_pos)
        self.wgAddress = self.add(npyscreen.TitleText, name="Website address:", begin_entry_at=entry_pos)
        self.wgInterval = self.add(npyscreen.TitleText, name="Check intervals:", begin_entry_at=entry_pos)

    def beforeEditing(self):
        self.wgName.value = ''
        self.wgAddress.value = ''
        self.wgInterval.value = ''

    def on_ok(self):
        # TODO If confirmed, ask if the user want to check the settings
        # TODO Check if the values seem to be correct (check if thats an int...), check if no empty values
        first_ping = npyscreen.notify_yes_no('Do you want to first ping the website?', 'Check', editw=1)
        if first_ping:
            npyscreen.notify_wait('Checking...')
        else:
            self.parentApp.websitesContainer.add([self.wgName.value, self.wgAddress.value, self.wgInterval.value])
            npyscreen.notify_confirm('Change saved!', editw=1)
        self.parentApp.switchForm('MAIN')

    def on_cancel(self):
        exiting = npyscreen.notify_yes_no('Are you sure you want to exit without saving?', editw=1)
        if exiting:
            npyscreen.notify('Your changes were NOT saved')
            self.parentApp.switchForm('MAIN')
        else:
            pass


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
    def create(self):
        self.value = None
        self.wgPager = self.add(npyscreen.TitlePager)

    def beforeEditing(self):
        self.wgPager.name = "Website " + str(self.value)
        self.wgPager.values = self.parentApp.websitesContainer.get_detailed_stats(self.value)

    def afterEditing(self):
        self.parentApp.switchForm('MAIN')


class MainForm(npyscreen.FormWithMenus, npyscreen.ActionFormMinimal):
    GRID_UPDATE_FREQ = 10
    # TODO Change the label of the OK button for something like EXIT if possible

    def create(self):
        self.wgWebsiteGrid = self.add(WebsiteGridWidget, name='Monitoring', max_height=25)
        self.wgAlertBox = self.add(AlertBoxWidget, name='Alerts', rely=30)

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
        self.wgWebsiteGrid.values = self.parentApp.websitesContainer.list_all_websites()
        self.wgWebsiteGrid.display()

        # TODO REMOVE - DEBUGGING PURPOSE
        self.wgAlertBox.add_line([str(self.parentApp.getHistory())])
        self.wgAlertBox.display()

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


if __name__ == '__main__':
    app = WebsiteMonitoringApplication()
    app.run()
