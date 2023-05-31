# Copyright 2023 - Yuksel Rudy Alkarem

import pandas as pd
from ROSCO_toolbox.ofTools.fast_io.FAST_reader import InputReader_OpenFAST
from ROSCO_toolbox.ofTools.fast_io.FAST_writer import InputWriter_OpenFAST
from ROSCO_toolbox.utilities import run_openfast
import os

class NervePhysical:
    def __init__(self, filename):
        self.data = pd.read_csv(filename)

    def get_data(self):
        return self.data

    # def get_channels(self):
    #     return self.data.columns
    #
    # def get_channel_data(self, column_name):
    #     return self.data[column_name]

class NerveVirtual:
    def __init__(self):
        pass

    def change_model_setup(self, fastfile, OF_filename, f_list,
                       v_list, des_v_list):
        fastin = InputReader_OpenFAST()
        fastout = InputWriter_OpenFAST()
        fastin.FAST_InputFile     = fastfile
        fastin.FAST_directory     = OF_filename
        fastout.FAST_namingOut    = fastin.FAST_InputFile[:-4]
        fastout.FAST_runDirectory = fastin.FAST_directory

        # read input files
        self.read_openfast_files(fastin, f_list)

        fastout.fst_vt = fastin.fst_vt

        # backup clean variables
        clean_variables = self.backup_clean_variables(f_list, v_list, fastin)

        # change variables
        for file, variable, desired in zip(f_list, v_list, des_v_list):
            if file in fastout.fst_vt and variable in fastout.fst_vt[file]:
                fastout.fst_vt[file][variable] = desired
            else:
                print(f"Error: Invalid file or variable specified: {file}, {variable}")


        # write output files
        self.write_openfast_files(fastout, f_list)
        return clean_variables, fastout

    def restore_model_setup(self, f_list, v_list, clean_variables, of_file):
        for file_name, variable, clean_value in zip(f_list, v_list, clean_variables):
            if file_name in of_file.fst_vt and variable in of_file.fst_vt[file_name]:
                of_file.fst_vt[file_name][variable] = clean_value
            else:
                print(f"Error: Invalid file or variable specified: {file_name}, {variable}")

        # write output files
        self.write_openfast_files(of_file, f_list)

    def backup_clean_variables(self, f_list, v_list, of_file):
        clean_variables = []
        for file_name, variable in zip(f_list, v_list):
            if file_name in of_file.fst_vt and variable in of_file.fst_vt[file_name]:
                clean_value = of_file.fst_vt[file_name][variable]
                clean_variables.append(clean_value)
            else:
                print(f"Error: Invalid file or variable specified: {file_name}, {variable}")

        return clean_variables

    @staticmethod
    def read_openfast_files(of_file, f_list):
        for file in f_list:
            if file == 'Fst':
                of_file.read_MainInput()
            elif file == 'ElastoDyn':
                of_file.read_ElastoDyn()
            elif file == 'HydroDyn':
                of_file.read_HydroDyn()
            elif file == 'ServoDyn':
                of_file.read_ServoDyn()
            else:
                print(f"Error: Undefined input file specified: {file}")

    @staticmethod
    def write_openfast_files(of_file, f_list):
        for file in f_list:
            if file == 'Fst':
                of_file.write_MainInput()
            elif file == 'ElastoDyn':
                of_file.write_ElastoDyn()
            elif file == 'HydroDyn':
                of_file.write_HydroDyn()
            elif file == 'ServoDyn':
                of_file.write_ServoDyn()
            else:
                print(f"Error: Undefined output file specified: {file}")


    def run_virtual(self, OF_filename, fastcall, fastfile):
        run_openfast(
            OF_filename,
            fastcall=fastcall,
            fastfile=fastfile,
            chdir=True
        )

    def output_manager(self, output_folder, output_file, of_file):
        # Moving output files to output directory (supports: .out, .outb, .MD.out)
        outdir = os.path.join(output_folder, output_file)

        if not os.path.isdir(outdir):
          os.makedirs(outdir)

        outname = of_file.FAST_namingOut + '.out'
        outbname = of_file.FAST_namingOut + '.outb'
        MDoutname = of_file.FAST_namingOut + '.MD.out'
        if os.path.isfile(os.path.join(of_file.FAST_runDirectory,outname)):
          os.rename(os.path.join(of_file.FAST_runDirectory,outname), os.path.join(outdir,outname))

        if os.path.isfile(os.path.join(of_file.FAST_runDirectory,outbname)):
          os.rename(os.path.join(of_file.FAST_runDirectory,outbname), os.path.join(outdir,outbname))

        if os.path.isfile(os.path.join(of_file.FAST_runDirectory,MDoutname)):
          os.rename(os.path.join(of_file.FAST_runDirectory,MDoutname), os.path.join(outdir,MDoutname))
