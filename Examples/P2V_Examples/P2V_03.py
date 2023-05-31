'''
----------- P2V_03 --------------
this example synchronizes P2B with V2B through three synchronizing rules.
-------------------------------------
Synchronizing Rules:
1- V always runs at the beginning with P
2- V always runs at the beginning of a new segment
3- Δt must be +ve at all times

In this example:
  - Initialize Brain, NervePhysical, and NerveVirtual simulatenuously
  - Define physical and virtual environments
  - Quantify synching quality with (SQ)

'''
# Python Modules
import os

# Digital Twin Modules
from DigiTWind.brain import Brain

# Digital Twin settings
twin_rate = 1.0

# Numerical Model Setup
TMax = 20

# Physical database name and directory
P_name      = 'test.csv'
this_dir    = os.path.dirname(os.path.abspath(__file__))
P_dir       = os.path.join(os.path.dirname(os.path.dirname(this_dir)), \
                          'Test_Cases','DigiTWind_Test_Cases','Physical')
P_filename  = os.path.join(P_dir,P_name)

# Virtual Model database name and directory
V_name           = "NREL_FOCAL_V1"  # where.fst lives
fastfile         = "DT1.fst"        # .fst file name
this_dir         = os.path.dirname(os.path.abspath(__file__))
V_dir            = os.path.join(os.path.dirname(os.path.dirname(this_dir)), \
                                'Test_Cases','Virtual')
V_filename      = os.path.join(V_dir, V_name)
fastcall         = os.path.join(os.path.dirname(os.path.dirname(this_dir)),
                                        'OpenFAST/install/bin','openfast')
f_list           = ['Fst']
v_list           = ['TMax']
des_v_list       = [TMax]

dt = Brain(twin_rate)
dt.load_pdata(P_filename)
dt.p2v_realize(P_filename, fastfile, fastcall, V_filename, f_list, v_list, des_v_list)
