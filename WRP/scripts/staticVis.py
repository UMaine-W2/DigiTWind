import sys
sys.path.append('../py-wrp')

from source.wrp import Params, WaveGauges, DataLoader, DataManager, WRP
import matplotlib.pyplot as plt
import time

if __name__ == "__main__":
    # initialize parameters with default settings
    pram = Params()

    # create wave gauge object and add gauges
    gauges = WaveGauges()
    gauges.addGauge(-4, .08083, "PXI1Slot5/ai2", 0)
    gauges.addGauge(-3.5, .10301, "PXI1Slot5/ai6", 0)
    gauges.addGauge(-2, .10570, "PXI1Slot5/ai4", 0)
    gauges.addGauge(-0, .08163, "PXI1Slot5/ai0", 1) # the '1' here indicates for prediction

    # create dm object which manages transferring data to wrp
    dm = DataManager(
        pram,
        gauges,
        readSampleRate=30,
        writeSampleRate=30,
        updateInterval = 1,
    )

# files to read statically
    load = DataLoader(
        'data/3.12.22.full.csv',
        'data/3.12.22.time.csv',
    )

    # initialize wrp
    wrp = WRP(gauges)

    # initialize plotter
    V = wrp.setVis(dm)

    time.sleep(5)
    # specify operation to be triggered whenever 'loading' data
    def callFunc(wrp, dm):
        global V
        # start_time = time.time()
        wrp.spectral(dm)
        wrp.inversion(dm)
        wrp.reconstruct(dm)
        # print(time.time() - start_time)
        wrp.updateVis(dm, V)
        plt.pause(.01)

    with plt.ion():
        load.generateBuffersDynamic(dm, wrp, 40, callFunc)
