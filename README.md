# Website availability & performance monitoring

This project is a python console program that has been made to monitor user-defined websites.
The user can add websites by adding them manually or by using the built-in import function, set check intervals, then leave the program regularly check the registered websites.

**Some of the features included:**

* Detailed statistics over different timeframes (availability, response time, status counts...).
* Logged alerts when one of the monitored websites has its availability going below 80%.
* Possibility to see the last header.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

This project has been written using Python 3. It has not been tested with Python 2. Due to the curses interface, it probably won't run on Windows.
It was developped and tested on MacOS. The program itself should also work just fine on Linux systems (I have tried it on Ubuntu). I have not thoroughly tested the testing scripts that are involving servers on the localhost on Ubuntu though.

### Installing

Start by cloning the repository. 

``` 
git clone https://github.com/ClementAcher/WebsiteMonitoring
cd WebsiteMonitoring/
```

**Optional**: You may then want to setup an environment before installing the requierements. Such thing can be done using virtualenv or Anaconda. If you have Anaconda installed, you can easily do so with the following lines.

```
conda create -n website-monitoring-env python=3.6
source activate website-monitoring-env
```

Then install the required libraries
```
pip install -r requirements.txt 
```

**Note:** Depending on the setup of your PATH, you may need to use pip3 instead of pip to get the Python 3 version.

And you are good to go!

### Running the program

To launch the program, just run the python file `./website_monitoring/core.py`

```
cd website_monitoring/
python core.py
```

**Note that the terminal window must be large enough to get the app running.**

Once the program is running, you can navigate through the widgets using `TAB` and `TAB+SHIFT`, selecting things using `ENTER` and open the menu of the main form using `CTRL+X`.

### Walkthrough  with an example

#### Main form

After launching the app, the main form will be displayed. This form contains a grid displaying all the websites currently monitored (empty when the app is started) with a few stats. The metrics of that grid are updated every 10 seconds.

The bottom part of that form contains a scrollable text box that will display all the alerts, an alert being website having its availability going below 80% for the last 2 minutes, or recovering from a previous alert.

Press `CTRL+X` to open the menu and select **Import websites**.

#### "Import websites" form

From here, you can pick a JSON file containing websites entries to quickly add websites to monitor. An entry needs 3 things:

* A name to identify the website
* The URL
* The check interval (int in seconds, > 0)

The repository comes with a sample demo file. You can find it at `WebsiteMonitoring/website_monitoring/file_to_import/example_import.json`. Import it using the field to pick a file.

#### Get detailed stats for a website

Once the import is done, you will be sent back to the main form, but this time, the grid won't be empty!
You can then select a website to see more information about it. Selecting one will open a new form.
From that form, you can pick a time frame to get different metrics over that time frame.

Note that this form is not automatically updated. The values are updated only when a time frame is selected.
You can close that form using the `OK` button.

#### Manually add websites

On the main form, press `CTRL+X` to get the menu, select **Add website**, and fill the empty fields!

## Running the tests

### Global behavior

#### `RunServers.py`

Since it is actually hard to find a website that is likely to be down from time to time, but not all the time
to test this program, I have added a script to create and run servers on the localhost that the
user can easily set whether those servers will time out or not.

To try this, run

```
cd tests
python RunServers.py
```

After choosing the number of server you want to run, a JSON file will automatically 
be created and added to the `file_to_import` folder, so that you can easily add them 
in the app!

#### `RandomStateServer.py`

RandomStateServer.py is a script similar to the previous one. It creates a server (and only one), that will automatically randomly timeout from time to time.

The probability of timing out is defined at the beginning of the Python script, and can be easily changed. It is initially set at 0.2, so that alerts will often be triggered.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details


