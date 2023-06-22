'''
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
'''
# Python Modules
import os

# Digital Twin Modules
from DigiTWind.brain import Brain

# Digital Twin settings
twin_rate = 1.0
TMax      = 20
channels  = ['Time', 'PtfmTDX', 'PtfmRDY']
# Physical database name and directory
P_name      = 'test.csv'
this_dir    = os.path.dirname(os.path.abspath(__file__))
P_dir       = os.path.join(os.path.dirname(os.path.dirname(this_dir)),
                            'Test_Cases','Physical')
P_filename  = os.path.join(P_dir,P_name)

dt = Brain(twin_rate, TMax, channels)
dt.load_pdata(P_filename)
dt.sync_pdata()
dt.print_sync_pdata()