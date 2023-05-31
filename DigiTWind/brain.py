# Copyright 2023 - Yuksel Rudy Alkarem

import numpy as np
import pandas as pd
import time

# Digital Twin Modules
from DigiTWind.nerve import NervePhysical, NerveVirtual

class Brain:
    def __init__(self, twin_rate):
        self.twin_rate = twin_rate
        self.pdata = None
        self.vdata = None
        self.interpolated_pdata = None
        self.interpolated_vdata = None

    def load_pdata(self, filename):
        self.pdata = NervePhysical(filename)

    def interpolate_pdata(self):
        df = self.pdata.get_data()
        t_interp = np.arange(df['Time'][0], df['Time'].iloc[-1]+self.twin_rate, self.twin_rate)
        new_df = pd.DataFrame()
        for channel in df.columns:
            data_interp = np.interp(t_interp, df['Time'], df[channel])
            new_df[channel] = data_interp
        new_df = new_df.loc[:, df.columns]
        self.interpolated_pdata = new_df

    def print_interpolated_pdata(self):
        for index, row in self.interpolated_pdata.iterrows():
            print(row)
            time.sleep(self.twin_rate)

    def run_vmodel(self, fastfile, fastcall, OF_filename, f_list, v_list, des_v_list):
        self.vdata = NerveVirtual()  # Create an instance of NerveVirtual
        clean_variables, of_file = self.vdata.change_model_setup(fastfile,
         OF_filename, f_list, v_list, des_v_list)
        self.vdata.run_virtual(OF_filename, fastcall, fastfile)
        self.vdata.restore_model_setup(f_list, v_list, clean_variables, of_file)
        self.vdata.output_manager(OF_filename, 'output', of_file)

    def p2v_realize(self, filename, fastfile, fastcall, OF_filename, f_list, v_list, des_v_list):
        self.load_pdata(filename)
        self.run_vmodel(fastfile, fastcall, OF_filename, f_list, v_list, des_v_list)
