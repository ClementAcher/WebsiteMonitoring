# -*- coding: utf-8 -*-
import npyscreen

# TODO Global settings : choose timeout?

class MyGrid(npyscreen.GridColTitles):
    def __init__(self, *args, **keywords):
        super(MyGrid, self).__init__(*args, **keywords)
        self.col_titles = ['Website', 'Interval Check', 'Status']

        # TODO Stop hard coding this
        l = [['https://www.google.com', '30', 'OK'],
             ['https://www.facebook.com', '100', 'No response']]
        self.values = l
        pass

    def custom_print_cell(self, actual_cell, cell_display_value):
        pass
        # TODO Do that properly
        # if cell_display_value =='FAIL':
        #    actual_cell.color = 'DANGER'
        # elif cell_display_value == 'PASS':
        #    actual_cell.color = 'GOOD'
        # else:
        #    actual_cell.color = 'DEFAULT'


class AddWebsiteForm(npyscreen.ActionForm):
    # TODO Make the form smaller to get something nicer
    def create(self):
        self.value = None
        entry_pos = 25
        # TODO Add line between
        self.wgName = self.add(npyscreen.TitleText, name="Entry name:", begin_entry_at=entry_pos)
        self.wgAddress = self.add(npyscreen.TitleText, name="Website address:", begin_entry_at=entry_pos)
        self.wgInterval = self.add(npyscreen.TitleText, name="Check intervals:", begin_entry_at=entry_pos)

    def on_ok(self):
        # TODO If confirmed, ask if the user want to check the settings
        first_ping = npyscreen.notify_yes_no('Do you want to first ping the website?', 'Check', editw=1)
        if first_ping :
            npyscreen.notify_wait('Checking...')
        else :
            npyscreen.notify_confirm('Change saved!', editw=1)
        self.parentApp.switchForm('MAIN')

    def on_cancel(self):
        exiting = npyscreen.notify_yes_no('Are you sure you want to exit without saving?', editw=1)
        if exiting:
            npyscreen.notify('Your changes were NOT saved')
            self.parentApp.switchForm('MAIN')
        else :
            pass

class MainForm(npyscreen.FormWithMenus):
    def create(self):
        # TODO Add the possibility to select a website and see more detailed stats
        self.grid_monitor = self.add(MyGrid, name='Monitoring')
        self.main_menu = self.new_menu(name='Main menu', shortcut='m')

        self.main_menu.addItem('Add new website', self.add_new_website, shortcut='a')

    def add_new_website(self):
        self.parentApp.getForm('ADD_WEBSITE').value = None
        self.parentApp.switchForm('ADD_WEBSITE')


class WebsiteMonitoringApplication(npyscreen.NPSAppManaged):
    def onStart(self):
        self.addForm('MAIN', MainForm)
        self.addForm('ADD_WEBSITE', AddWebsiteForm)


if __name__ == '__main__':
    app = WebsiteMonitoringApplication()
    app.run()
