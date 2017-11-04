# Website availability & performance monitoring

This project is a python console program that has been made to monitor user-defined websites.
The user can add websites by adding them manually or by using the import function, set check intervals, then leave the program regularly check the registered websites.

**Some of the features included:**

* Detailed statistics over different timeframes (availability, response time, status counts...).
* Logged alerts when one of the monitored websites has its availability going below 80%.
* Possibility to see the last header.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

This project has been written using Python 3. It has not been tested with Python 2. Due to the curses interface, it probably won't run on Windows.

### Installing

Start by cloning the repository. 

``` 
git clone https://github.com/ClementAcher/WebsiteMonitoring
cd WebsiteMonitoring/
```

*Optional*: You may then want to setup an environment before installing the requierements. If you have Anaconda installed, you can easily do so with the following lines.

```
conda create -n website-monitoring-env python=3.6
source activate website-monitoring-env
```

Then install the required libraries
```
pip install -r requirements.txt 
```

And you are good to go!

### Running the program

To launch the program, just run the python file `./website_monitoring/core.py`

```
cd website_monitoring/
python core.py
```

**Note that the terminal window must be big enough to get the app running.**

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

The repository comes with a sample demo file. You can find it at `WebsiteMonitoring/website_monitoring/file_to_import/import.json`. Import it using the field to pick a file.

#### Get detailed stats for a website

Once the import is done, you will come back to the main form, but this time, the grid won't be empty!
You can then select a website to see more information about it. Selecting one will open a new form.
From that form, you can pick a time frame to get different metrics over that time frame.

Note that this form is not automatically updated. The values are updated only when a time frame is selected.
You can close that form using the `OK` button.

#### Manually add websites

On the main form, press `CTRL+X` to get the menu, select **Add website**, and fill the empty fields!

## Running the tests

TODO

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details


