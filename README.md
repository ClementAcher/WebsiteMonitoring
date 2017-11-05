# Website availability & performance monitoring

This project is a python console program that has been made to monitor user-defined websites.
The user can add websites by adding them manually or by using the built-in import function, 
set check intervals, then leave the program regularly check the registered websites.

**Some of the features included:**

* Detailed statistics over different timeframes (availability, response time, status counts...).
* Logged alerts when one of the monitored websites has its availability going below 80% for the past 2 minutes.
* Possibility to see the last header.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

This project has been written using Python 3. It has not been tested with Python 2. Due to the curses interface, it probably won't run on Windows.
It was developed and tested on MacOS. The program itself should also work just fine on Linux systems (I have tried it on Ubuntu). 
I have not thoroughly tested the testing scripts that are involving servers on the localhost on Ubuntu though.

### Installing

Start by cloning the repository. 

``` 
git clone https://github.com/ClementAcher/WebsiteMonitoring
cd WebsiteMonitoring/
```

**Optional**: You may then want to setup an environment before installing the requirements. 
Such thing can be done using virtualenv or Anaconda. 
If you have Anaconda installed, you can easily do so with the following lines.

```
conda create -n website-monitoring-env python=3.6
source activate website-monitoring-env
```

Then install the required libraries
```
pip install -r requirements.txt 
```

**Note:** Depending on the setup of your PATH, you may need to use pip3 instead of pip to get the Python 3 version.
The same remark goes for the following commands between python and python3.

And you are good to go!

### Running the program

To launch the program, just run the python file `./website_monitoring/core.py`

```
cd website_monitoring/
python core.py
```

**Note that the terminal window must be large enough to get the app running.**

Once the program is running, you can navigate through the widgets using `TAB` and `TAB+SHIFT`, 
selecting things using `ENTER` and open the menu of the main form using `CTRL+X`.

### Walkthrough  with an example

#### Main form

After launching the app, the main form will be displayed. This form contains a scrollable grid displaying all the websites currently 
monitored (empty when the app is started) with a few stats. The metrics on that grid are updated every 10 seconds
except for the "last hour" metrics that are updated every minute.

The bottom part of that form contains a scrollable text box that will display all the alerts, an alert being website 
having its availability going below 80% for the last 2 minutes, or recovering from a previous alert.
Those alerts are also logged using the logging Python module in the log folder. 

**Note:** Setting the level of logging to DEBUG will also log the network errors! This can be set in `monitoring.py`.

Press `CTRL+X` to open the menu and select **Import websites**.

#### "Import websites" form

From here, you can pick a JSON file containing websites entries to quickly add websites to monitor. An entry needs 3 things:

* A name to identify the website
* The URL
* The check interval (int in seconds, > 0)

The repository comes with a sample demo file. You can find it at `WebsiteMonitoring/website_monitoring/file_to_import/example_import.json`. Import it using the field to pick a file.

**Note:** **Make sure to import proper files**. For efficiency reasons, the URLs won't be checked during the import.
This is yet done when the websites are added manually.

#### Get detailed stats for a website

Once the import is done, you will be sent back to the main form, but this time, the grid won't be empty!
You can then select a website to see more information about it. Selecting one will open a new form.
From that form, you can pick a time frame to get the different metrics corresponding.

Note that this form is not automatically updated. The values are updated only when a time frame is selected.
You can close that form using the `OK` button.

#### Manually add websites

On the main form, press `CTRL+X` to open the menu, select **Add website**, and fill the empty fields!

**Note:** it will check that the parameters and the URL are valid, but the website will be added even though there is already
the same entry.

#### Extra notes

- **Please don't resize the terminal window while the app is running.** It probably won't crash, but it can create some weird
visual bugs.

- Press `TAB` and `SHIFT+TAB` to navigate through the widgets. But for some unexplained reasons, once the alert box is 
selected, it is not possible to back to the grid using `SHIFT+TAB`. I have implemented a workaround: you can press `T`
to get the grid in focus.

- If you can't see the website you just added in the grid, it is probably just hidden. The grid is scrollable, check if 
it not at the bottom!

- The "last hour" stats are only updated every minute, while the rest of the grid is updated every 10 seconds. It explains why
the max of the last hour can be momentarily below the max of the last 10 minutes. That is also why you may have "No data" displayed
in those columns after adding a website for a couple seconds.

## Running the tests

### Global behavior

#### `RunServers.py`

Since it is actually hard to find a website that is likely to be down from time to time to test this application, 
I have added a script to create and run servers on the localhost that the user can easily set to down or up.

To try this, run

```
cd tests
python RunServers.py
```

After choosing the number of server you want to run, a JSON file will automatically 
be created and added to the `file_to_import` folder, so that you can easily add them 
in the app!

#### `RandomStateServer.py`

RandomStateServer.py is a script similar to the previous one. It creates a server (and only one), 
that will automatically randomly timeout from time to time.

The probability of timing out is defined at the beginning of the Python script, and can be easily changed. 
It is initially set at 0.2, so that alerts will often be triggered.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details


