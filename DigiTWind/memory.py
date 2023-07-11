# Copyright 2023 - Yuksel Rudy Alkarem

import multiprocessing as mp
import os
import pandas as pd


class Memory:
    def __init__(self, channels, t_max, twin_rate):
        self.channels           = channels
        self.t_max              = t_max
        self.twin_rate          = twin_rate
        self.manager            = mp.Manager()  # Create a Manager
        self.shared_ptime       = self.manager.Value('d', 0.0) # Create a shared dictionary for the physical time
        self.shared_vtime       = self.manager.Value('d', 0.0) # Create a shared dictionary for the virtual time
        self.shared_pdata       = self.manager.dict() # Create a shared dictionary for the physical data
        self.shared_vdata       = self.manager.dict() # Create a shared dictionary for the virtual data
        self.vdata_list         = self.manager.list()  # Use the Manager to create the list for virtual data
        self.sync_pdata_df      = None
        self.sync_vdata_df      = None
        # Fidelity Testing
        self.mirrcount          = {channel: 0.0 for channel in self.channels} # Mirroring count for fidelity testing
        self.mirrcoeff          = self.manager.dict({channel: 0.0 for channel in self.channels}) # Mirroring coefficient for fidelity testing
        self.mirrcoeff_t        = {channel: [] for channel in self.channels[1:]}   # Mirroring coefficient as a function of time
        self.total_error_dict   = self.manager.dict({channel: 0 for channel in
                            channels[1:]})  # Initiate total_error_dict with zeros for all channels
        self.current_error_dict = self.manager.dict({channel: 0 for channel in
                            channels[1:]})
    def fidelity_test(self, error, tol, channel):
        if error < tol:
            self.mirrcount[channel] += 1

        self.mirrcoeff[channel] = self.mirrcount[channel] / (self.t_max / self.twin_rate + 1) * 1e2
        self.mirrcoeff_t[channel].append(self.mirrcoeff[channel])

    def write_mirrcoeff_t(self, filename="mirrcoeff_t.csv"):
        # Check if the directory exists and create it if necessary
        outdir = "output"
        if not os.path.exists(outdir):
            os.makedirs(outdir)

        # Creating DataFrame from mirrcoeff_t dictionary
        df = pd.DataFrame(self.mirrcoeff_t)

        # Writing DataFrame to CSV
        df.to_csv(os.path.join(outdir, filename), index=False)

    def report_fidelity(self):
        for channel, total_error in self.total_error_dict.items():
            print(f"Total error for {channel}: {total_error}")
            print(f"mirroring coefficient for {channel}: {self.mirrcoeff[channel]}")
            print(f"mirroring coefficient in time for {channel}: {self.mirrcoeff_t[channel]}")