# -*- coding: utf-8 -*-
import npyscreen
import monitoring


# TODO

class WebsiteGrid(npyscreen.GridColTitles):
    def __init__(self, *args, **keywords):
        super(WebsiteGrid, self).__init__(*args, **keywords)
        self.col_titles = ['Website', 'Interval Check', 'Status']
        # TODO It is possible to set the number of columns
        # TODO Stop hard coding this
        self.values = self.fill_grid()
        self.select_whole_line = True

    def actionHighlighted(self, act_on_this, keypress):
        print(act_on_this, keypress)

    def set_up_handlers(self):
        super(WebsiteGrid, self).set_up_handlers()
        self.handlers["^O"] = self.action_selected

    def action_selected(self, inpt):
        print(self.selected_row())

    def custom_print_cell(self, actual_cell, cell_display_value):
        pass
        # TODO Do that properly
        # if cell_display_value =='FAIL':
        #    actual_cell.color = 'DANGER'
        # elif cell_display_value == 'PASS':
        #    actual_cell.color = 'GOOD'
        # else:
        #    actual_cell.color = 'DEFAULT'

    def fill_grid(self):
        l = self.parent.parentApp.websitesContainer.websites
        return l


class AlertBox(npyscreen.TitlePager):
    def __init__(self, *args, **keywords):
        super(AlertBox, self).__init__(*args, **keywords)
        self.values = [["""{} Website website is down. availability=availablility, time=time""".format(i)] for i
                       in range(100)]


class AddWebsiteForm(npyscreen.ActionForm):
    # TODO Make the form smaller to get something nicer
    def create(self):
        self.name = "New Website"
        entry_pos = 25
        # TODO Add line between
        self.wgName = self.add(npyscreen.TitleText, name="Entry name:", begin_entry_at=entry_pos)
        self.wgAddress = self.add(npyscreen.TitleText, name="Website address:", begin_entry_at=entry_pos)
        self.wgInterval = self.add(npyscreen.TitleText, name="Check intervals:", begin_entry_at=entry_pos)

    def beforeEditing(self):
        self.wgName.value = ''
        self.wgAddress.value = ''
        self.wgInterval.value = ''

    def on_ok(self):
        # TODO If confirmed, ask if the user want to check the settings
        # TODO Check if the values seem to be correct (check if thats an int...)
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


class MainForm(npyscreen.FormWithMenus):
    def create(self):
        # TODO Add the possibility to select a website and see more detailed stats
        self.grid_monitor = self.add(WebsiteGrid, name='Monitoring', max_height=25)
        self.alert_box = self.add(AlertBox, name='Alerts', rely=30)

        self.main_menu = self.new_menu(name='Main menu')
        self.website_menu = self.new_menu(name='Website menu')


        self.main_menu.addItem('Add new website', self.add_new_website, shortcut='a')

    def add_new_website(self):
        self.parentApp.getForm('ADD_WEBSITE').value = None
        self.parentApp.switchForm('ADD_WEBSITE')




class WebsiteMonitoringApplication(npyscreen.NPSAppManaged):
    def onStart(self):
        self.websitesContainer = monitoring.WebsitesContainer()
        self.addForm('MAIN', MainForm)
        self.addForm('ADD_WEBSITE', AddWebsiteForm)


if __name__ == '__main__':
    # helpers.hello()
    app = WebsiteMonitoringApplication()
    app.run()
