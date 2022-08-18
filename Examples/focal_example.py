'''
----------- Ex1 --------------
Load a turbine, tune a controller, run OpenFAST simulation
-------------------------------------

In this example:
  - Load a turbine from OpenFAST
  - Tune a controller
  - Run an OpenFAST simulation

'''
# Python Modules
import yaml
import os
import numpy as np
import matplotlib.pyplot as plt
# ROSCO toolbox modules
from ROSCO_toolbox.utilities import write_DISCON, run_openfast

this_dir = os.path.dirname(os.path.abspath(__file__))
example_out_dir = os.path.join(this_dir,'examples_out')

if not os.path.isdir(example_out_dir):
  os.makedirs(example_out_dir)


# Run OpenFAST
# --- May need to change fastcall if you use a non-standard command to call openfast
fastcall = os.path.join(this_dir,'../OpenFAST/install/bin','openfast')
run_openfast(
  os.path.join(this_dir,path_params['FAST_directory']),
  fastcall=fastcall,
  fastfile=path_params['FAST_InputFile'],
  chdir=True
  )




