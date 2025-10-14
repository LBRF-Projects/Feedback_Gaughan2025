# Simulated Feedback During Motor Imagery - Gaughan 2025

This repository contains the experiment code for a study exploring whether simulated drawing feedback can facilitate learning via motor imagery during a complex motor task.

![tracelab_animation](tracelab_heart.gif)

This study uses a modified version of the TraceLab task from [Ingram et al. (2018)](https://doi.org/10.1016/j.bbr.2018.10.030) that consists of 5 sessions: 4 sessions of 5 blocks of motor imagery training, plus a final session with 5 blocks of imagery training followed by 5 more blocks of physical drawing to measure task performance.

Instead of practicing with random and repeated shapes (as done in the original study), this version of the task uses three different repeated shapes during training, each with a different type of trial feedback. For the first shape, the participant is shown the target shape at the end of the trial with simulated feedback overlayed. For the second shape, the participant is just shown the target shape as a reference. For the third shape, the participant is shown no feedback. In the final session of the task, the participant is tested on their tracing performance for the 3 shapes along with random shapes to measure the relative benefit of feedback type on shape learning.

More information on task and how it works can be found in the [main TraceLab repository](https://github.com/LBRF/TraceLab).


## Requirements

This study requires the following hardware to work as intended:

* A computer with Python 3.9 or later installed
* A touchscreen monitor

However, the task will still run without a touchscreen (in development mode or with `force_show_cursor` set to True in params.py) for testing and demonstration purposes.


## Getting Started

This TraceLab experiment is written in Python 3 (3.9+ compatible) using the [KLibs framework](https://github.com/a-hurst/klibs). It should install and run on any recent version of macOS, Linux, or Windows.


### Installing Dependencies

#### Option 1: Pipenv Installation

To install all of the task's Python dependencies in a self-contained virtual environment, run the following commands in a terminal window inside the same folder as this README:

```bash
pip install pipenv
pipenv install
```
These commands should create a fresh environment for the TraceLab project with all its dependencies installed inside it. Note that to run commands using this environment, you will need to prefix them with `pipenv run`, e.g. `pipenv run klibs run 24`.

#### Option 2: Global Installation

Alternatively, to install the dependencies for the task in your global Python environment, run the following commands in a terminal window:

```bash
pip install https://github.com/a-hurst/klibs/releases/latest/download/klibs.tar.gz
```


### Running TraceLab

TraceLab is a KLibs experiment, meaning that it is run using the `klibs` command at the terminal (running the 'experiment.py' file using `python` directly will not work, and will print a warning).

To run the experiment, navigate to the TraceLab folder in Terminal and run `klibs run [screensize]`,
replacing `[screensize]` with the diagonal size of your display in inches (e.g. `klibs run 24` for a 24-inch monitor). If you just want to test the program out for yourself and skip demographics collection, you can add the `-d` flag to the end of the command to launch the experiment in development mode.


## Exporting Data

The data recorded by TraceLab can be split into two groups: **figure & tracing data**, and **participant & trial data**. Scripts for importing, joining, and analyzing both groups of data can be found in the [TraceLabAnalysis](https://github.com/LBRF/TraceLabAnalysis/) repository.

Details on the figure and tracing data formats can be found in the [main TraceLab repository](https://github.com/LBRF/TraceLab). All other data collected in TraceLab is neatly organized in an SQL database. To export this data from TraceLab, simply run

```
klibs export
```

while in the TraceLab directory. This will export the trial data from all participants into individual tab-delimited text files for each participant in the project's `ExpAssets/Data` subfolder.

Data from any participants that did not complete all of their sessions will be saved to the `ExpAssets/Data/incomplete` folder.


