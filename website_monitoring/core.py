# -*- coding: utf-8 -*-
import npyscreen
import monitoring


# TODO

# WIDGETS

class WebsiteGrid(npyscreen.GridColTitles):
    # TODO Annoying thing: to exit the grid you need to press tab. Overwrite h_... to leave the grid when at the end
    def __init__(self, *args, **keywords):
        super(WebsiteGrid, self).__init__(*args, **keywords)
        self.col_titles = ['Website', 'Interval Check', 'Status']
        # TODO It is possible to set the number of columns
        # TODO Stop hard coding this
        self.values = self.fill_grid()
        self.select_whole_line = True
        self.handlers["^O"] = self.action_selected

    def action_selected(self, inpt):
        """Open a form for more stats about the website"""
        self.parent.parentApp.getForm('WEBSITE_INFO').value = self.edit_cell[0]
        self.parent.parentApp.switchForm('WEBSITE_INFO')

    def custom_print_cell(self, actual_cell, cell_display_value):
        pass

    def fill_grid(self):
        l = self.parent.parentApp.websitesContainer.list_all_websites()
        return l


class AlertBox(npyscreen.TitlePager):
    def __init__(self, *args, **keywords):
        super(AlertBox, self).__init__(*args, **keywords)
        self.values = [["""{} Website website is down. availability=availablility, time=time""".format(i)] for i
                       in range(100)]


# FORMS

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


class WebsiteInfoForm(npyscreen.Form):
    def create(self):
        self.value = None
        self.wgPager = self.add(npyscreen.TitlePager)

    def beforeEditing(self):
        self.wgPager.name = "Website " + str(self.value)
        self.wgPager.values = self.parentApp.websitesContainer.get_website(self.value)

    def afterEditing(self):
        self.parentApp.switchForm('MAIN')


class MainForm(npyscreen.FormWithMenus):
    def create(self):
        # TODO Add the possibility to select a website and see more detailed stats
        self.wgWebsiteGrid = self.add(WebsiteGrid, name='Monitoring', max_height=25)
        self.wgAlertBox = self.add(AlertBox, name='Alerts', rely=30)

        self.main_menu = self.new_menu(name='Main menu')

        self.main_menu.addItem('Add new website', self.add_new_website, shortcut='a')

    def add_new_website(self):
        self.parentApp.getForm('ADD_WEBSITE').value = None
        self.parentApp.switchForm('ADD_WEBSITE')

    def beforeEditing(self):
        self.update_grid()

    def update_grid(self):
        self.wgWebsiteGrid.values = self.parentApp.websitesContainer.list_all_websites()
        self.wgWebsiteGrid.display()

    def on_ok(self):
        self.parentApp.switchForm(None)

# APP

class WebsiteMonitoringApplication(npyscreen.NPSAppManaged):
    def onStart(self):
        self.websitesContainer = monitoring.WebsitesContainer()
        self.addForm('MAIN', MainForm)
        self.addForm('ADD_WEBSITE', AddWebsiteForm)
        self.addForm('WEBSITE_INFO', WebsiteInfoForm)


if __name__ == '__main__':
    app = WebsiteMonitoringApplication()
    app.run()
