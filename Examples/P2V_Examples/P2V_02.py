'''
----------- P2V_02 --------------
this example runs the numerical model and prints it on a twin rate frequency
-------------------------------------

In this example:
  - Define a twin rate
  - Define virtual database name and directory
  - Run the virtual model (change settings, runs, restores)
'''
# Python Modules
import os
import numpy as np

# Digital Twin Modules
from DigiTWind.brain import Brain

# Digital Twin settings
twin_rate = 1.0

# Numerical Model Setup
TMax = 20

# Virtual Models database name and directory
# FAST
V_name           = "NREL_FOCAL_V1"  # where.fst lives
fastfile         = "DT1.fst"        # .fst file name
this_dir         = os.path.dirname(os.path.abspath(__file__))
V_dir            = os.path.join(os.path.dirname(os.path.dirname(this_dir)), \
                               'Test_Cases','DigiTWind_Test_Cases','Virtual')
V_filename       = os.path.join(V_dir, V_name)
fastcall         = 'openfast'
f_list           = ['Fst']
v_list           = ['TMax']
des_v_list       = [TMax]

dt = Brain(twin_rate)
dt.run_vmodel(fastfile, fastcall, V_filename, f_list, v_list, des_v_list)
