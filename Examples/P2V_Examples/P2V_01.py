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
TITLE         = "DigiTWind"                 # Name of the digital twin
TEST_NAME     = "P2V_01"                    # Name of the test
SCALE         = 70                          # Froude scale of experimental data
TWIN_RATE     = 1.0                         # Twin rate
T_MAX         = 10                          # Total run time
CH1PZDRFT     = 0.7112                      # Physical mean drift in Surge displacement
CH1VZDRFT     = 3.21                        # Virtual mean drift in Surge displacement
CH2PZDRFT     = 1.2556                      # Physical mean drift in Pitch displacement
CH2VZDRFT     = -0.272                      # Virtual mean drift in Pitch displacement
CH1_TOL       = 2.0                         # Surge displacement error tolerance
CH2_TOL       = 0.0433                      # Pitch displacement error tolerance
PHYSICAL_ENV  = True                        # Physical environment mode
VIRTUAL_ENV   = False                       # Virtual environment mode
GUI           = False                       # Graphical User Interface mode

# Digital Twin settings

dtw_settings = {
    'title'        : TITLE,
    'test_name': TEST_NAME,
    'time_settings': {
            'twin_rate': TWIN_RATE,
            't_max'    : T_MAX
    },
    'channel_info': {
            'Time'   : {'unit': 's', 'scale': SCALE},
            'PtfmTDX': {'unit': 'm', 'scale': SCALE, 'Pzdrift': CH1PZDRFT, 'Vzdrift': CH1VZDRFT, 'tol': CH1_TOL},
            'PtfmRDY': {'unit': 'deg', 'scale': SCALE, 'Pzdrift': CH2PZDRFT, 'Vzdrift': CH2VZDRFT, 'tol': CH2_TOL},
    },
    'modes': {
            'physical_env': PHYSICAL_ENV,
            'virtual_env' : VIRTUAL_ENV,
            'gui'         : GUI
    }
}

# Physical database name and directory
P_name      = 'test.csv'
this_dir    = os.path.dirname(os.path.abspath(__file__))
P_dir       = os.path.join(os.path.dirname(os.path.dirname(this_dir)),
                            'Test_Cases','Physical')
P_filename  = os.path.join(P_dir,P_name)

dtw = Brain(dtw_settings)
dtw.metrolize(filename=P_filename)