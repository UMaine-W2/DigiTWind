"""
----------- P2V_01 --------------
this example reads the experimental data and prints it on a twin rate frequency
-------------------------------------

In this example:
  - Define a twin rate
  - Define physical database name and directory
  - Load csv file containing physical data
  - create a new empty dataframe store interpolated results
  - interpolate results based on the twin rate
  - print physical data at every twin rate.
"""

# Python Modules
import os

# Digital Twin Modules
from DigiTWind.brain import Brain

# CONSTANTS
# General:
TITLE         = "DigiTWind"                 # Name of the digital twin
TEST_NAME     = "P2V_01"                    # Name of the test
SCALE         = 70                          # Froude scale of experimental data
TWIN_RATE     = 1.0                         # Twin rate
T_MAX         = 10                          # Total run time
TOL           = 0.00                        # error tolerance (percentage of experimental std)

# Modes:
PHYSICAL_ENV  = True                        # Physical environment mode
VIRTUAL_ENV   = False                       # Virtual environment mode
GUI           = False                       # Graphical User Interface mode

# Digital Twin settings

dtw_settings = {
    'title'                : TITLE,
    'test_name'            : TEST_NAME,
    'time_settings': {
            'twin_rate'    : TWIN_RATE,
            't_max'        : T_MAX
    },
    'channel_info' : {
        'scale'            : SCALE,
        'TNAME'            : ['Time', 'PtfmTDX', 'PtfmRDY'], # Technical channel name
        'LNAME'            : ['Time', 'Surge', 'Pitch'],     # user-friendly channel name
        'UNIT'             : ['s', 'm', 'deg']               # channel units
    },
    'modes'         : {
            'physical_env': PHYSICAL_ENV,
            'virtual_env' : VIRTUAL_ENV,
            'gui'         : GUI
    },
    'tol'                 : TOL
}

# Physical database name and directory
P_name      = 'test.csv'
this_dir    = os.path.dirname(os.path.abspath(__file__))
P_dir       = os.path.join(os.path.dirname(os.path.dirname(this_dir)),
                            'Test_Cases','Physical')
P_filename  = os.path.join(P_dir,P_name)

dtw = Brain(dtw_settings)
dtw.metrolize(filename=P_filename)