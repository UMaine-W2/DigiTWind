"""
----------- P2V_03 --------------
this example synchronizes P2B with V2B
-------------------------------------

In this example:
  - Provide digital twin settings
  - Define physical database name and directory
  - Setup numerical Model variables
  - load yaml file
  - Define virtual database name and directory (FAST+ROSCO)
  - Run P2V metrology with both physical and virtual mode turned on
  - Run the virtual model (change settings, runs in parallel with ZMQ, restores)
  - Compare with physical data and print local errors at every twin rate and global error in the end.
"""

# Python Modules
import os
from ROSCO_toolbox.inputs.validation import load_rosco_yaml

# Digital Twin Modules
from DigiTWind.brain import Brain, ModelConfig

# Digital Twin settings
SCALE = 70
time_settings = {
    'twin_rate': 1.0,
    'TMax'     : 10
}
channel_info = {
    'Time': {'unit': 's', 'scale': SCALE},
    'PtfmTDX': {'unit': 'm', 'scale': SCALE, 'Pzdrift': 0.7112, 'Vzdrift': 3.21, 'tol': 2.0},
    'PtfmRDY': {'unit': 'deg', 'scale': SCALE, 'Pzdrift': 1.2556, 'Vzdrift': -0.272, 'tol': 0.0433},
}
modes = {'p_on': True, 'v_on': True} # Physical Mode = On. Virtual Mode = Off


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
des_v_list       = [time_settings['TMax']]
# ROSCO DISCON LIBRARY
lib_name         = os.path.join(this_dir,'../../ROSCO/ROSCO/build/libdiscon.so')
param_filename   = os.path.join(V_filename, 'controller', 'DISCON.IN')

# Run Virtual model in parallel with ZMQ
model_config = ModelConfig(fastfile, fastcall, V_filename, f_list, v_list,
    des_v_list, lib_name, param_filename)

dt = Brain(time_settings, channel_info, modes)
dt.p2v_metrolize(filename=P_filename,
                 model_config=model_config,
                 turbine_params=turbine_params,
                 turbine_name=turbine_name,
                 controller_params=controller_params)