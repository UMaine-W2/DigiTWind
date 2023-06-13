# Copyright 2023 - Yuksel Rudy Alkarem

import numpy as np
import pandas as pd
import time
import multiprocessing as mp

# Digital Twin Modules
from DigiTWind.nerve import NervePhysical, NerveVirtual

class Brain:
    def __init__(self, twin_rate, TMax):
        self.twin_rate  = twin_rate
        self.TMax       = TMax
        self.pdata      = None
        self.vdata      = None
        self.sync_pdata = None
        self.sync_vdata = None
        self.real_time  = 0.0

    def load_pdata(self, filename):
        self.pdata = NervePhysical(filename)

    def sync_pdata(self):
        df = self.pdata.get_data()
        t_interp = np.arange(df['Time'][0], df['Time'].iloc[-1]+self.twin_rate, self.twin_rate)
        new_df = pd.DataFrame()
        for channel in df.columns:
            data_interp = np.interp(t_interp, df['Time'], df[channel])
            new_df[channel] = data_interp
        new_df = new_df.loc[:, df.columns]
        self.sync_pdata = new_df

    def print_sync_pdata(self):
        for index, row in self.sync_pdata.iterrows():
            print(row)
            time.sleep(self.twin_rate)

    def run_vmodel(self, model_config, turbine_params, turbine_name, controller_params):
        self.vdata = NerveVirtual(self.twin_rate)  # Create an instance of NerveVirtual
        self.vdata.update_twin_rate(model_config.param_filename, turbine_params, turbine_name, controller_params)
        clean_variables, of_file = self.vdata.change_model_setup(
            model_config.fastfile,
            model_config.OF_filename,
            model_config.f_list,
            model_config.v_list,
            model_config.des_v_list)

        # Run ZeroMQ (P1) and OpenFAST(P2) in parallel
        p1 = mp.Process(target=self.vdata.run_zmq)
        p2 = mp.Process(target=self.vdata.run_virtual, args=(
            model_config.OF_filename,
            model_config.fastcall,
            model_config.fastfile,
            model_config.lib_name,
            model_config.param_filename))
        p3 = mp.Process(target=self.print_sync_vdata)

        p1.start()
        p2.start()

        # Let the initiation finishes
        time.sleep(5)
        p3.start()

        p1.join()
        p2.join()
        p3.join()

        self.vdata.restore_model_setup(
            model_config.f_list,
            model_config.v_list,
            clean_variables, of_file)
        self.vdata.output_manager(
            model_config.OF_filename,
            'output', of_file)

    def print_sync_vdata(self):
        while self.real_time <= self.TMax:
            print(self.real_time)
            print(self.vdata.shared_dict[self.real_time])
            time.sleep(self.twin_rate)
            self.real_time += self.twin_rate

class ModelConfig:
    def __init__(self, fastfile, fastcall, OF_filename, f_list, v_list, des_v_list, lib_name, param_filename):
        self.fastfile = fastfile
        self.fastcall = fastcall
        self.OF_filename = OF_filename
        self.f_list = f_list
        self.v_list = v_list
        self.des_v_list = des_v_list
        self.lib_name = lib_name
        self.param_filename = param_filename
