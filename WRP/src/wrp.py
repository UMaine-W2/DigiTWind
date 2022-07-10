import numpy as np
from scipy.signal import welch
from scipy import linalg
import matplotlib.pyplot as plt
from numpy import genfromtxt
import time


class WaveGauges:
    """The information needed to a interpret a physical wave measurement
    
    Contains lists with the physical locations, calibration constants, analog
    port, and role in the WRP algorithm, which can be either `measurement` or 
    `validation`. The latter also indicates the physical location of the float.
    Position is defined where waves move in positive x direction and x = 0 at the
    validation gauge.

    Attributes:
        xPositions: list of physical locations
        calibrationSlopes: list of conversion factors from measurement to wave height, (m/V)
        portNames: list of channels on which to aquire data from this wave gauge
        wrpRole: list of roles, 0 indicates measurement, 1 indicates validation
    """
    def __init__(self):
        """Set up lists for pertinent wave gauge information
        """
        self.xPositions = []
        self.calibrationSlopes = []
        self.portNames = []
        self.wrpRole = []      # 0 = measurement gauge, 1 = prediction gauge

    def addGauge(self, position, slope, name, role):
        """Adds details for an individual gauge to class

        Args:
            position: physical location in space, meters
            slope: conversion factor for measurement m/V
            name: analog channel/ address, string
            role: 0 for measurement, 1 for validation

        """
        self.xPositions.append(position)
        self.calibrationSlopes.append(slope)
        self.portNames.append(name)
        self.wrpRole.append(role)

    def nGauges(self):
        """Determine number of gauges which have been added"""
        return(len(self.xPositions))

    def measurementIndex(self):
        """Find indices of gauges used for measurement
        
        Returns:
            A list of indices
        """
        mg = [i for i, e in enumerate(self.wrpRole) if e == 0]
        return mg

    def predictionIndex(self):
        """Find indices of gauges used for validation
        
        Returns:
            A list of indices
        """
        pg = [i for i, e in enumerate(self.wrpRole) if e != 0]
        return pg

class Params:
    """Parameters which alter the inversion and reconstruction process
    
    Attributes:
        ta: reconstruction assimilation time
        ts: spectral assimilation time
        nf: number of frequencies to use for reconstruction
        mu: threshold parameter to determine fastest/slowest 
            group velocities for prediction zone
        lam: regularization parameter for least squares fit
    """
    def __init__(self):
        # wrp parameters
        self.ta = 10            # 
        self.ts = 30            # 
        self.nf = 100           # 
        self.mu = 0.05          # 
        self.lam = 1            # 


class DataManager:
    """Facilitates data allocation to wrp and control
    
    Args:
        pram: Params instance
        gauges: WaveGauges instance
        readSampleRate: frequency to read
        writeSampleRate: frequency to write
        updateInterval: spacing between callback

    
    """

    def __init__(self, pram, gauges, readSampleRate, writeSampleRate, updateInterval):

        self.readSampleRate = readSampleRate    # frequency to take wave measurements (Hz)
        self.writeSampleRate = writeSampleRate  # frequency to send motor commands (Hz)

        self.preWindow = 0          # number of seconds before assimilation to reconstruct for
        self.postWindow = 5        # number of seconds after assimilation to reconstruct for

        # should eventually be based on the actual (calculated) prediction zone
        self.updateInterval = updateInterval     # time between grabs at new data (s)
        
        # number of channels from which to read
        self.nChannels = gauges.nGauges()

        # time interval between wave measurements (s)
        self.readDT = 1 / self.readSampleRate
        self.writeDT = 1 / self.writeSampleRate

        # initialize read and write based on desired interval between samples
        self.addUpdateInterval()

        # set up buffer - samples, values, time -
        self.bufferNSamples = self.readSampleRate * pram.ts
        self.bufferValues = np.zeros((self.nChannels, self.bufferNSamples), dtype=np.float64) 
        self.bufferTime = np.arange(-pram.ts, 0, self.readDT)

        # set up validation - samples, values, time -
        self.validateNSamples = self.readSampleRate * (pram.ta + self.preWindow + self.postWindow)
        self.validateNFutureSamples = self.readSampleRate * self.postWindow
        self.validateNPastSamples = self.readSampleRate * (pram.ta + self.preWindow)
        self.validateValues = np.zeros((self.nChannels, self.validateNSamples), dtype=np.float64)
        self.validateTime = np.arange(-pram.ta - self.preWindow, self.postWindow, self.readDT)

        # array to save results of inversions for the length of time to visualize in the future
        self.inversionNSaved = int(self.postWindow / self.updateInterval) + 1
        self.inversionSavedValues = np.zeros((2, self.inversionNSaved, pram.nf))

        # number of samples for reconstruction
        self.assimilationSamples = pram.ta * self.readSampleRate

        # gauges to select for reconstruction
        self.mg = gauges.measurementIndex()

        # gauges for prediction
        self.pg = gauges.predictionIndex()

        # alter calibration constants for easy multiplying
        self.calibrationSlopes = np.expand_dims(gauges.calibrationSlopes, axis = 1)

 
    def addUpdateInterval(self):
        """Initialize read and write - samples, values, time - based on update interval
        """

        # set up read - samples, values, time -
        self.readNSamples = self.readSampleRate * self.updateInterval
        self.readValues = np.zeros((self.nChannels, self.readNSamples), dtype=np.float64)
        self.readTime = np.arange(0, self.updateInterval, self.readDT)

        # set up write - samples, values, time -
        self.writeNSamples = self.writeSampleRate * self.updateInterval
        self.writeValues = np.zeros((self.writeNSamples), dtype=np.float64) 
        self.writeTime = np.arange(0, self.updateInterval, self.writeDT)        

        # set up predict - samples, values, time - 
        self.predictNSamples = self.writeNSamples * self.updateInterval
        self.predictValues = np.zeros(self.predictNSamples, dtype = np.float64)
        self.predictTime = np.arange(0, self.updateInterval, self.writeDT)

    def bufferUpdate(self, newData):
        """adds new data to the end of bufferValues, shifting existing data and removing the oldest
        
        Args:
            newData: array of new data collected with length readNSamples
        """
        # shift old data to the end of the matrix
        self.bufferValues = np.roll(self.bufferValues, -self.readNSamples)
        # write over old data with new data
        self.bufferValues[:, -self.readNSamples:] = newData

    def validateUpdate(self, newData):
        """adds new data to the end of validateValues, shifting existing data and removing the oldest
        
        Args:
            newData: array of new data collected with length readNSamples
        """
        # shift old data to the end of the matrix
        self.validateValues = np.roll(self.validateValues, -self.readNSamples)
        
        # write over old data with new data
        self.validateValues[:, -self.readNSamples:] = newData

    def inversionUpdate(self, a, b):
        """adds most recent inversion to the end ofinversionSavedValues, deletes the oldest
        
        Args:
            a: array of weights for cosine
            b: array of weights for sine
        """
        # array to save backlog of inversion results, good for validating real time
        self.inversionSavedValues = np.roll(self.inversionSavedValues, -1, axis = 1)

        # need to squeeze to fit it into the matrix
        self.inversionSavedValues[0][self.inversionNSaved - 1] = np.squeeze(a)
        self.inversionSavedValues[1][self.inversionNSaved - 1] = np.squeeze(b)


    def inversionGetValues(self, method):
        """retrieves inversion values for a specified `method`
        
        Args: 
            method: string
                'oldest' -> values for validation
                'newest' -> most recent values for prediction
        
        Returns:
            a: array of weights for cosine
            b: array of weights for sine
        """
        # need expand_dims for the matrix math in reconstruct

        if method == 'oldest':
            a = np.expand_dims(self.inversionSavedValues[0][0][:], axis=1)
            b = np.expand_dims(self.inversionSavedValues[1][0][:], axis=1)

            return a,b

        if method == 'newest':
            a = np.expand_dims(self.inversionSavedValues[0][-1][:], axis=1)
            b = np.expand_dims(self.inversionSavedValues[1][-1][:], axis=1)

            return a,b

    def reconstructionData(self):
        """gets data from bufferValues which should be used for reconstruction
        
        Calls preprocessing to scale and center data on mean

        Returns:
            An array of processed data for reconstruction
        """
        # select measurement gauges across reconstruction time
        data = self.bufferValues[self.mg, -self.assimilationSamples:]

        processedData = self.preprocess(data, self.mg)
        return processedData

    def reconstructionTime(self):
        """gets time to use for reconstruction
        
        Returns:
            Array of time values for reconstruction
        """
        time = self.bufferTime[-self.assimilationSamples:]
        return time

    def spectralData(self):
        """gets data from bufferValues which should be used as spectral data
        
        Calls preprocessing to scale and center data on mean

        Returns:
            An array of processed data for spectral information
        """
        data = self.bufferValues[self.mg, :]

        processedData = self.preprocess(data, self.mg)
        return processedData

    def validateData(self):
        """prepares validation data through preprocessing step
        
        Returns:
            processed data for validation
        """
        data = self.validateValues[self.pg, :]

        processedData = self.preprocess(data, self.pg)
        return processedData

    def preprocess(self, data, whichGauges):
        """scales data by calibration constants and subtracts the mean
        
        Args: 
            data: array of values to be processed
            whichGauges: the indices of the gauges which correspond to the data being processed
        
        Returns: 
            array of processed data
        """
        # scale by calibration constants
        data *= self.calibrationSlopes[whichGauges]

        # center on mean
        dataMeans = np.expand_dims(np.mean(data, axis = 1), axis = 1)
        data -= dataMeans

        return data



class DataLoader:
    """Hands data from a static file to DataManager
    
    Args:
        dataFile: location of csv file with wave measurements, samples 
                    are columns and locations are rows
        timeFile: csv of time stamps associated with dataFile
    """
    def __init__(self, dataFile, timeFile):
        # location of data
        self.dataFileName = dataFile
        # load full array
        self.dataFull = genfromtxt(self.dataFileName, delimiter=',')

        # location of data
        self.timeFileName = timeFile
        # load full array
        self.timeFull = genfromtxt(self.timeFileName, delimiter=',')

        # location in full array for dynamic method
        self.currentIndex = 0

        # location in full array for dynamic soft method
        self.bufferCurrentIndex = 0
        self.validateCurrentIndex = 0

    def generateBuffersStatic(self, flow, reconstructionTime):
        """Goes to specified time in static file and assigns data accordingly
        
        Args: 
            flow: instance of DataManager
            reconstructionTime: time at which to reconstruct
        """
        # load reconstruction and validation data one time

        # index of the specified reconstruction time
        self.reconstructionIndex = np.argmin( np.abs(reconstructionTime - self.timeFull))
        bufferLowIndex = self.reconstructionIndex - flow.bufferNSamples
        bufferHighIndex = self.reconstructionIndex

        validateLowIndex = self.reconstructionIndex - flow.validateNPastSamples
        validateHighIndex = self.reconstructionIndex + flow.validateNFutureSamples

        flow.bufferValues = self.dataFull[:, bufferLowIndex:bufferHighIndex]
        flow.validateValues = self.dataFull[:, validateLowIndex:validateHighIndex]

    def generateBuffersDynamic(self, flow, wrp, reconstructionTime, callFunc):
        """Reads data file in chunks
        
        Starts from beginnign of file, and iterates through assigning each 
        chunk to the stored buffers as it goes. Calls a function at each
        step.
        
        Args: 
            flow: instance of DataManager
            wrp: instance of WRP
            reconstructionTime: time at which to stop taking data
            callFunc: function to call at every step
        """
        # index of the specified reconstruction time
        self.reconstructionIndex = np.argmin( np.abs(reconstructionTime - self.timeFull))

        while self.currentIndex <= self.reconstructionIndex:
            if self.currentIndex == 0:

                filler = np.reshape(np.cos(flow.bufferTime + np.random.normal()), (1, flow.bufferNSamples))
                fillAll = np.tile(filler, (4, 1))
                flow.bufferValues = fillAll

                newData = self.dataFull[:, :flow.readNSamples]

            else:              
                newData = self.dataFull[:, self.currentIndex:self.currentIndex + flow.readNSamples]
            
            flow.bufferUpdate(newData)
            flow.validateUpdate(newData)

            # decide what to do on update in main script
            callFunc(wrp, flow)

            self.currentIndex += flow.readNSamples

    def generateBuffersDynamicSoft(self, flow, reconstructionTime):
        # called 'soft' because it still allocates data to the right place in each buffer, 
        # unlike true acquisition which needs to do reconstruction as soon as data is available

        # index of the specified reconstruction time
        self.reconstructionIndex = np.argmin( np.abs(reconstructionTime - self.timeFull))

        # add samples from self.dataFull to flow.validateValues until the number of samples added
        # matches flow.validateNFutureSamples
        flow.validateValues[:, -flow.validateNFutureSamples:] = self.dataFull[:, :flow.validateNFutureSamples]
        self.validateCurrentIndex = flow.validateNFutureSamples

        while self.bufferCurrentIndex < self.reconstructionIndex:
            if self.bufferCurrentIndex == 0:
                bufferNewData = self.dataFull[:, :flow.readNSamples]
                flow.bufferUpdate(bufferNewData)

            # update bufferValues and validateValues
            bufferNewData = self.dataFull[:, self.bufferCurrentIndex: self.bufferCurrentIndex+flow.readNSamples]
            flow.bufferUpdate(bufferNewData)

            validateNewData = self.dataFull[:, self.validateCurrentIndex: self.validateCurrentIndex+flow.readNSamples]
            flow.validateUpdate(validateNewData)

            self.bufferCurrentIndex += flow.readNSamples
            self.validateCurrentIndex += flow.readNSamples

        print(flow.bufferValues)

class WRP(Params):
    """Implements methods of wave reconstruction and propagation

    Args: 
        gauges: instance of WaveGauges
    """
    def __init__(self, gauges):
        super().__init__()

        self.x = gauges.xPositions
        self.calibration = gauges.calibrationSlopes

        # gauges to select for reconstruction
        self.mg = gauges.measurementIndex()

        # gauges for prediction
        self.pg = gauges.predictionIndex()

        # important spatial parameters for wrp based on gauge locations
        self.xmax = np.max( np.array(self.x)[self.mg] )
        self.xmin = np.min( np.array(self.x)[self.mg] )
        self.xpred = np.array(self.x)[self.pg]

        self.plotFlag = False

    def spectral(self, flow):
        """Calculates spectral information

        Uses spectral data to create a set of spectral attributes including \n
            - T_p: peak period
            - k_p: peak wavenumber
            - m0: zero moment of the spectrum
            - Hs: significant wave height
            - cg_fast, cg_slow: fastest and slowest group velocity
            - xe, xb: spatial reconstruction parameters
            - k_min, k_max: wavenumber bandwidth for reconstruction

        Args:
            flow: instance of DataManager
        """
        # assign spectral variables to wrp class
        data = flow.spectralData()

        f, pxxEach = welch(data, fs = flow.readSampleRate)
        pxx = np.mean(pxxEach, 0)
  
        # added 0.01 because warning when divide by zero
        self.T_p = 1 / (f[pxx == np.max(pxx)] + 0.01)

        # peak wavelength
        self.k_p = (1 / 9.81) * (2 * np.pi / self.T_p)**2

        # zero-th moment as area under power curve
        self.m0 = np.trapz(pxx, f)

        # significant wave height from zero moment
        self.Hs = 4 * np.sqrt(self.m0)

        self.w = f * np.pi * 2

        thresh = self.mu * np.max(pxx)

        # set anything above the threshold to zero
        pxx[pxx > thresh] = 0
        # plt.plot(f, pxx)
        # find the locations which didn't make the cut
        pxxIndex = np.nonzero(pxx)[0]

        # find the largest gap between nonzero values
        low_index = np.argwhere( (np.diff(pxxIndex) == np.max(np.diff(pxxIndex))) )[0][0]
        high_index = pxxIndex[low_index + 1]

        # plt.axvline(x = f[low_index])
        # plt.axvline(x = f[high_index])
        # plt.show()

        # select group velocities
        if self.w[low_index] == 0:
            self.cg_fast = 20 # super arbitrary
        else:
            self.cg_fast = (9.81 / (self.w[low_index] * 2))
        self.cg_slow = (9.81 / (self.w[high_index] * 2))

        # spatial parameters for reconstruction bandwidth
        self.xe = self.xmax + self.ta * self.cg_slow
        self.xb = self.xmin

        # reconstruction bandwidth wavenumbers
        self.k_min = 2 * np.pi / (self.xe - self.xb)
        self.k_max = 2 * np.pi / min(abs(np.diff(self.x)))

    def inversion(self, flow):
        """Find linear weights for surface representation

        Calculates an array of wavenumbers and corresponding deep water
        frequencies. Solves least squares optimization to get best fit
        surface representation. Adds results of inversion to a saved 
        array in DataManager called inversionSavedValues.

        Args:
            flow: instance of DataManager
        """
    # define wavenumber and frequency range
        k = np.linspace(self.k_min, self.k_max, self.nf)
        w = np.sqrt(9.81 * k)

    # get data
        eta = flow.reconstructionData()
        t = flow.reconstructionTime()
        x = np.array(self.x)[self.mg]

    # grid data and reshape for matrix operations
        X, T = np.meshgrid(x, t)

        self.k = np.reshape(k, (self.nf, 1))
        self.w = np.reshape(w, (self.nf, 1))

        X = np.reshape(X, (1, np.size(X)), order='F')

        T = np.reshape(T, (1, np.size(T)), order='F')        
        eta = np.reshape(eta, (np.size(eta), 1))

        psi = np.transpose(self.k@X - self.w@T)

        
    # data matrix
        Z = np.zeros((np.size(X), 2*self.nf))
        Z[:, :self.nf] = np.cos(psi)
        Z[:, self.nf:] = np.sin(psi)


        m = np.transpose(Z)@Z + (np.identity(self.nf * 2) * self.lam)
        n = np.transpose(Z)@eta
        weights, res, rnk, s = linalg.lstsq(m, n)

        # choose all columns [:] for future matrix math
        a = weights[:self.nf,:]
        b = weights[self.nf:,:]

        flow.inversionUpdate(a, b)


    def reconstruct(self, flow):
        """Reconstructs surface using saved inversion values
        
        Calculates upper and lower limit time boundary for reconstruction time.
        Calculates shape of reconstructed surface for both validation and 
        prediction and saves them as attributes of DataManager. The former 
        is saved as DataManager.reconstructedSurfaceValidate and the latter as
        DataManager.reconstructedSurfacePredict

        Args:
            flow: instance of DataManager
        """
# General
        # prediction zone time boundary
        self.t_min = (1 / self.cg_slow) * (self.xpred - self.xe)
        self.t_max = (1 / self.cg_fast) * (self.xpred - self.xb)

        # matrix for summing across frequencies
        sumMatrix = np.ones((1, self.nf))

# Reconstruct for validation
        # dx array for surface representation at desired location
        dxValidate = self.xpred * np.ones((1, flow.validateNSamples))

        # time for matrix math
        tValidate = np.expand_dims(flow.validateTime, axis = 0)

        aValidate, bValidate = flow.inversionGetValues('oldest')

        acosValidate = aValidate * np.cos( (self.k @ dxValidate) - self.w @ tValidate )
        bsinValidate = bValidate * np.sin( (self.k @ dxValidate) - self.w @ tValidate )
        
        self.reconstructedSurfaceValidate = sumMatrix @ (acosValidate + bsinValidate)

# Reconstruct for prediction
        # dx array for surface representation at desired location
        dxPredict = self.xpred * np.ones((1, flow.predictNSamples))

        tPredict = np.expand_dims(flow.predictTime, axis = 0)
        aPredict, bPredict = flow.inversionGetValues('newest')

        acosPredict = aPredict * np.cos( (self.k @ dxPredict) - self.w @ tPredict )
        bsinPredict = bPredict * np.sin( (self.k @ dxPredict) - self.w @ tPredict )
        
        self.reconstructedSurfacePredict = np.squeeze(sumMatrix @ (acosPredict + bsinPredict))
    def setVis(self, flow):
        # plt.ion()
        figure, ax = plt.subplots(figsize = (8,5))
        plt.ylim([-.2, .2])
        ax.axvline(0, color = 'gray', linestyle = '-', label = 'reconstruction time')
        reconstructedLine, = ax.plot(flow.validateTime, np.zeros(flow.validateNSamples), color = 'blue', label = 'reconstructed')
        measuredLine, = ax.plot(flow.validateTime, np.zeros(flow.validateNSamples), color = 'red', label = 'measured')
        tMin = ax.axvline(-1, color = 'black', linestyle = '--', label = 'reconstruction boundary')
        tMax = ax.axvline(1, color = 'black', linestyle = '--')
        plt.title("Reconstruction and propagation loaded incrementally")
        plt.xlabel("time (s)")
        plt.ylabel("height (m)")
        ax.legend(loc = 'upper left')
        V = figure, ax, reconstructedLine, measuredLine, tMin, tMax

        return V

    def updateVis(self, flow, V):

        figure, ax, reconstructedLine, measuredLine, tMin, tMax = V

        reconstructedLine.set_ydata(np.squeeze(self.reconstructedSurfaceValidate))
        measuredLine.set_ydata(np.squeeze(flow.validateData()))
        tMin.set_xdata(self.t_min)
        tMax.set_xdata(self.t_max)

        figure.canvas.draw()
        figure.canvas.flush_events()





    def filter(self):
        # do some lowpass filtering on noisy data
        pass
    def update_measurement_locations(self):
        # hold the locations x in the wrp class and update them if necessary
        pass
