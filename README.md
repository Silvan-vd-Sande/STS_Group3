# CreaTe M8: Sensor Technology in Sports
This is the git repository for Creative Technology, Module 8, Sensor
Technology in Sports. It contains the files you will need to 
connect the Movella DOT sensors to your laptop using Python. 

> [!NOTE]
> This repository was written for Windows operating systems.
If you are using a Linux operating system, please contact one of the teachers or TAs.<br>
>The Bluetooth connection of the DOT sensors is not compatible with macOS. However, you can emulate saved data using emulate_controller.


Anne Haitjema, Bouke Scheltinga, Jonathan Matarazzi, Frank Bosman, Daan Doeleman, Matei Obrocea <br>
Last updated: 17-03-2026

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#dot-sensors">DOT sensors</a>
    </li>
    <li>
      <a href="#repository-installation ">Repository installation </a>
    </li>
   <li>
      <a href="#general-structure ">General structure </a>
    </li>
    <li>
        <a href="#usage">Usage</a>
        <ol>
            <li><a href="#initializing-the-sensors">Initializing the sensors</a></li>
            <li><a href="#starting-and-stopping-the-connection-to-the-sensor">Starting and stopping the connection to the sensor</a></li>
            <li><a href="#process-incoming-data">Process incoming data</a></li>
            <li><a href="#plotting-data">Plotting data</a></li>
            <li><a href="#accessing-variables-thread-safe">Accessing variables (thread safe)</a></li>
            <li><a href="#building-your-feedback-mechanism">Building your feedback mechanism</a></li>
        </ol>
    </li>
  </ol>
</details>

## DOT sensors
The DOT sensors are inertial measurement units (IMUs) that measure the acceleration, 
the angular velocity, and the magnetic field. They have an embedded sensor fusion algorithm
that calculates the 3D orientation and free acceleration of the IMU. 
Detailed information about the DOT sensor can be found in the [user manual](https://www.xsens.com/hubfs/Downloads/Manuals/Xsens%20DOT%20User%20Manual.pdf). 
The most important information is described here as well. 

There are 20 DOT sensors available for this course, they are numbered DOT-01 through DOT-20.
Every group will get 2 DOT sensors for the project. The DOT sensors have an LED, a power button, 
and a micro-USB port that is used for charging (see the figure below). **These sensors are expensive, so handle them with care.** 

![](images/DOT.png)

DOT 1-10 cannot be turned on using the power button, but must be turned on by plugging in the charging cable. 
DOT 11-20 can be turned on by pressing the power button until the LED starts blinking. 
All DOTs can be turned off by pressing the power button until the LED stops blinking. 

The DOT sensors measure in their own coordinate system, called the sensor coordinate system (see the figure below).
There is also a local coordinate system, in which the x-axis points east, the y-axis points north, 
and the z-axis points up. 

- The acceleration, angular velocity and magnetic field output are in the sensor coordinate system. 
- The orientation and free acceleration output are in the local coordinate system.

![](images/DOT_CS.png)

Currently, the DOT sensors output the orientation (in Euler angles), the free acceleration, 
and the angular velocity. In some cases, it might be possible to switch to other outputs. Please contact Bouke, Anne or 
one of the TAs if you want to switch to another output mode. The available output modes (called Payload modes)
are listed [here](https://www.xsens.com/hubfs/Downloads/Manuals/Xsens%20DOT%20BLE%20Services%20Specifications.pdf) 
in sections 3.2, 3.3 and 3.4 (p. 12-14). It is not possible to active multiple output modes simultaneously.


## Repository installation 
1. Fork this repository and clone it to a local folder.
   1. Click on the 'Fork' button in the top right corner, or the button below.
      - [![Fork Repository](https://img.shields.io/badge/Fork_This_Repo-GitLab-orange?style=for-the-badge&logo=gitlab)](https://gitlab.utwente.nl/bss_development/education/create_m8_sts/-/forks/new)
   2. Add the year and your group number to the name of the repository, for example: `create_m8_sts_2026_group_01`.
   3. Clone the repository to your local machine using the command line or Pycharm.
      - See [this tutorial](https://www.jetbrains.com/help/pycharm/set-up-a-git-repository.html) for more information on how to do this in Pycharm.
2. Set up a new python **3.9** virtual environment. The DOT tutorial contains a more detailed explanation of how to do this. In short:
   1. In Pycharm, go to interpreter settings.
   2. 'add interpreter' -> 'add local interpreter'.
   3. Type: 'Virtualenv' (or any other if you prefer).
   4. Base python: 'python 3.9'
   5. Click 'OK'.
   6. Verify you are using the correct interpreter in the bottom right corner of Pycharm.
3. Install requirements of this repository using 
```pip install -r requirements.txt```
4. Open `template.py` and replace `"DOT-01", "DOT-02"` with your sensor name(s).
5. Turn the sensors and **your bluetooth** on.
6. Run `template.py`.
7. Read <a href="#usage">'Usage'</a> to learn how the code works.

> [!NOTE] Note:
> If you are using Pycharm, disable `show plots in tool window` in the settings. Otherwise, the plots will not be updated.

> [!WARNING] Important:
> Terminate your program by closing the plot window using the red cross in the top right corner, **not by stopping the program in Pycharm**.
> Otherwise, the connection to the sensors will not be properly closed, and you might have trouble reconnecting to them.
> If this happens, turn the sensors off and on again.

## General structure
The general structure of the repository is as follows. There shouldn't be a need for you to modify any of the files or folders except for `template.py`, which is the starting point for your project.
```
├── controllers/        # DO NOT MODIFY, Underlying sensor logic
├── data/               # Folder containing recorded .csv files for emulation
├── examples/           # Some examples
├── images/             # Images used in this README
├── wheel_files/        # SDK for the DOT sensors, provided by Movella
├── template.py         # Your starting point! Edit this file to build your project
├── requirements.txt    # Python dependencies
└── README.md           # This instruction file
```

## Usage
This code base offers two ways to interact with the DOT sensors: 1) Connecting to the sensor(s) and plotting the data in real-time, and 2) emulating the sensor(s) using a pre-recorded data file.
These functionalities are available through extending the `DotController` and `EmulateController` classes, respectively. 
It can be very useful to record a datafile and use it together with the emulator. This allows you to easily evaluate the effects of changes in your code. 

> [!NOTE] Tip:
> Record your data using the record flag so you can emulate it later. Read <a href="#dotcontroller-options">DotController options</a> for more information

### Initializing the sensors
As shown in `template.py`, the code for your project should start with a class that connects to the sensors.
Extend the `DotController` class for live data or the `EmulateController` for recorded data, they are interchangeable and can be swapped out easily.

Within your class, you need to specify a number of things:
- `sensor_ids`: A list of sensor names, like `["DOT-04"]` or `["DOT-04", "DOT-18"]`.
- `plot_type`: The type of plot, it can either be `'custom', 'ori', 'acc', 'gyr', or 'disabled'`. For 'custom' you will have to supply `setup_plot` and `update_plot` inside your class.
- `record_data`: A true/false value indicating whether you want to record the current connection. This parameter is only useful when using the `DotController`, but leaving it in for the emulator will not break it.

A short example of how to initialize the sensors can be found below, it creates a custom class called 'Project' which will receive live updates from the sensor and show an acceleration plot.
```python
class Project(DotController):
    def __init__(self, sensor_ids):  
        super().__init__(sensor_ids, plot_type='acc', record_data=False)
```

### Starting and stopping the connection to the sensor
To execute the code, an instance of your class must be created, followed by starting the sensor connection. This can be achieved by:
```python
controller = Project(["DOT-01", "DOT-02"])  # Live connection to the sensors
controller.start()
```
For the emulator, recorded .csv data files are passed instead of sensor IDs:
```python
controller = Project(["./data/logfile_DOT-07_2025-05-07_14-05.csv", "./data/logfile_DOT-08_2025-05-07_14-05.csv"])  # Use recorded data
controller.start()
```

The connection to the sensor should also be properly stopped using the following at the end of your code:
```python
controller.stop()  # stops the connection to the sensor, and waits for the plot to be closed (if active)
```

### Processing incoming data
The project involves filtering or performing calculations on the sensor data. To implement custom processing logic, add the `process_data` method to the extended class
```python
def process_data(self, sensor_id, timestamp, ori, acc, gyr, sample_time, queue_size):
    self.processed_data[sensor_id].append(max(acc))  # Example: saving the maximum acceleration value
```
This example adds the processed data to a dictionary. Note that this dictionary must be initialized in your class constructor (`__init__` method) using: `self.processed_data = {sensor_id: [] for sensor_id in self.sensor_ids}`.

> [!WARNING]
> To access variables modified inside `process_data` from outside the main class (or outside `setup_plot` and `update_plot`), use setter and getter functions annotated with `@thread_safe`. 
> Read <a href="#use-variables-outside-thread-safe">'Use variables outside (thread safe)'</a> for detailed instructions.

### Plotting data
Besides the 3 default plots, it is also possible to add your own plotting logic. This is very useful for plotting your filtered data. 

To create a custom plot, two specific methods must be added to the extended class: `setup_plot`, which runs once to initialize the figure, and `update_plot`, which runs continuously after process_data to draw the data.

The only strict requirement for `setup_plot` is that it must initialize a `self.fig` variable containing the plot figure. The minimum valid implementation is as follows:
```python
def setup_plot(self):
    self.fig, self.axes = plt.subplots(1,1)

def update_plot(self, frame):
    pass
```
Note: that any data intended for plotting must first be stored and updated within the `process_data` method.
An example can be found in `examples/plotting.py`.

### Accessing variables (thread safe)
Because the underlying logic handles multiple threads to integrate the sensors, variables cannot be directly accessed outside the predefined methods (`process_data`, `setup_plot`, `update_plot`).
To safely retrieve variables externally, a getter method must be created. This is a function that simply returns the requested variable, but is annotated (preceded) by the `@BaseController.thread_safe` decorator.
This adds some internal logic to ensure that the variable is accessed safely across threads. The same applies for modifying a variable, then use a setter function with the annotation.

```python
@BaseController.thread_safe
def get_processed_data(self):
   # Note: if processed_data is a mutable variable (like a list or dictionary), you have to return a copy.
   return copy.deepcopy(self.processed_data)
```
Once defined, this method can be called anywhere; either inside your class using `self.get_processed_data()` or outside using `controller.get_processed_data`.

### Building your feedback mechanism
When plotting is enabled (i.e., plot_type is set to anything other than _'disabled'_), the `controller.start()` function blocks the main thread. 
Consequently, any code located after `controller.start()` will not execute until the plot window is manually closed.
An easy fix for this is to not use live plotting while using your feedback mechanism and set the plot_type to _'disabled'_. 
In case you want to use live plotting and a feedback mechanism at the same time, you can run your feedback mechanism in a separate thread by overriding the `feedback` function. 
The code snippet below shows how to implement it:

```python
def feedback(self):
   processed_data = self.get_processed_data()  # Use the getter to safely access the processed data
   print(f"{len(processed_data)} data points have been processed so far")
   time.sleep(0.1)  # Sleep for a short time to allow data retrieval/processing from the sensors
```


As long as you use this structure you should not have any problems with threads and can forget about their existence for a bit longer.
If you do want to mess around with them, ask a TA, and they will help you further.
