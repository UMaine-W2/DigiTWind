.. _how_to_run_OL:

How to Run
============================

In this section, we will provide an example on how to use the Open Loop method
to change the stiffness and damping values mid-simulation. The wave loading is
a pink noise. The main python driver for this example is found in :doc:`/DTFOWT/Examples/fPN1_OL.py`.

In this example:
  - Loop through freq. selection approach (FSA)
  - Load a default .yaml file
  - Modify .yaml file
  - Save the new .yaml file
  - Load OpenFAST input files
  - Modify OpenFAST input files for writing DISCON.IN file
  - Write DISCON.IN file
  - Revert back to clean input files
  - Modify OpenFAST input files for the simulation Setup
  - Run OpenFAST from ROSCO with StC_Mode=2 [reads K & C values from an external file]
  - Revert back to clean input files

The FSA illustrates different methods for calculating stiffness and matrices and
is outside the scope here. The main focus is how to load yaml file, change it, and save
it in with a new name like this:

.. code-block:: python

  # Load yaml file
  YAML = load_yaml(os.path.join(tune_dir,old_yaml))

  # Change yaml file
  YAML['controller_params']['StC_Mode'] = 2
  YAML['controller_params']['StC_Z_filename'] = os.path.abspath(os.path.join(this_dir,'../Tune_Cases/KC_values',KC_files[i]))

  # save yaml file
  save_yaml(tune_dir, new_yaml, YAML)


In this example the values for K and C values are already computed and saved in
:doc:`/DTFOWT/Tune_Cases/KC_values`.

The pink noise wave elevation is also pre-computed and can be found in :doc:`/DTFOWT/Test_Cases/wave_elevs/PN`
and is refered to in the python driver as follows:

.. code-block:: python

  fastout.fst_vt['HydroDyn']['WvKinFile'] = os.path.abspath(os.path.join(fastin.FAST_directory,'../wave_elevs/PN',WSE))

The OpenFAST model input files and setup are also provided in the 'Test_Cases' directory.

When the simulation is run, output files will be extracted to an output file in the 'Examples' directory.
One can extract the output file and check the TMD position to investigate the influence of stiffness and damping variation in has on the motion.
