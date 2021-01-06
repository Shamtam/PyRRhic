# PyRRhic
A Python-based RomRaider derivative

## Getting Started with Development

1. Install Python 3.8 32-bit (32-bit is necessary for J2534 drivers)
2. Clone repository (including submodules) to directory of your choice
3. In the repository top level directory, setup the virtual environment
    to the directory `./venv`:

```
.../PyRRhic/ $ python -m venv venv
```

4. Activate the virtual environment, and install all required libraries
```
.../PyRRhic/ $ ./venv/Scripts/activate
(venv) .../PyRRhic/ $ python -m pip install -r requirements.txt
```

5. [_**Optional, but recommended**_] VSCode settings have been included
    in the repository. To use them, simply open the root directory of
    the repository in VSCode as a folder. Settings include the debug
    launch configurations, and some basic settings to facilitate style
    consistencies (e.g. vertical rulers at 72 and 79 chars, per PEP8,
    auto-trim whitespace, 4 spaces as tabs, etc.)

## Starting PyRRhic
To start the program from command-line, simply call it as a module:
```
.../PyRRhic/ $ python -m pyrrhic
```
