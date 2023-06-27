'''
----------- P2V_03 --------------
this example synchronizes P2B with V2B
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
from ROSCO_toolbox.inputs.validation import load_rosco_yaml

# Digital Twin Modules
from DigiTWind.brain import Brain, ModelConfig

# Digital Twin settings
twin_rate = 1.0
TMax      = 10
channels  = ['Time', 'PtfmTDX', 'PtfmRDY']
p_on      = True # Physical Mode is On
v_on      = True # Virtual Mode is On

# Physical database name and directory
P_name      = 'test.csv'
this_dir    = os.path.dirname(os.path.abspath(__file__))
P_dir       = os.path.join(os.path.dirname(os.path.dirname(this_dir)),
                            'Test_Cases','Physical')
P_filename  = os.path.join(P_dir,P_name)

# Numerical Model Setup

# Load yaml file
this_dir           = os.path.dirname(os.path.abspath(__file__))
tune_dir           = os.path.join(this_dir, '../../Tune_Cases')
parameter_filename = os.path.join(tune_dir, 'NREL_FOCAL_V2.yaml')
inps               = load_rosco_yaml(parameter_filename)
path_params        = inps['path_params']
turbine_params     = inps['turbine_params']
controller_params  = inps['controller_params']

# Virtual Models database name and directory
# FAST
fastfile         = path_params['FAST_InputFile']
turbine_name, _  = os.path.splitext(fastfile)
V_filename       = path_params['FAST_directory']
fastcall         = os.path.join(this_dir,'../../OpenFAST/install/bin','openfast')
f_list           = ['Fst']
v_list           = ['TMax']
des_v_list       = [TMax]
# ROSCO DISCON LIBRARY
lib_name         = os.path.join(this_dir,'../../ROSCO/ROSCO/build/libdiscon.so')
param_filename   = os.path.join(V_filename, 'controller', 'DISCON.IN')

# Run Virtual model in parallel with ZMQ
model_config = ModelConfig(fastfile, fastcall, V_filename, f_list, v_list,
    des_v_list, lib_name, param_filename)

dt = Brain(twin_rate, TMax, channels, p_on, v_on)
dt.p2v_metrology(filename=P_filename,
                 model_config=model_config,
                 turbine_params=turbine_params,
                 turbine_name=turbine_name,
                 controller_params=controller_params)
# dt.p2v_realization()