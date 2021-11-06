# -*- coding: utf-8 -*-
"""
Created on Wed Oct 21 09:08:58 2020

@author: Kamil
"""

import numpy as np
from matplotlib import pyplot as plt
import fir_filter

def PlotWaveform(title, ycords):
    plt.figure()
    plt.title(title) 
    plt.xlabel('Time') 
    plt.ylabel('Amplitude') 
    plt.plot(ycords)  

    
def PlotECGWaveforms(title, yAxisFirstGraph, yAxisSecondGraph): 
    fig, axs = plt.subplots(2)
    fig.suptitle(title)
    axs[0].plot(yAxisFirstGraph)
    axs[1].plot(yAxisSecondGraph)
    
    
""" Plot frequency vs amplitude graph using two sets of values """
def PlotFrequency(title, samplingFrequency, fftCoefficients):
    # Scale x-axis to sampling frequency 
    frequencyAxis = np.linspace(0, samplingFrequency, len(fftCoefficients) )

    plt.figure()
    # Plot Frequency spectrum
    plt.plot( frequencyAxis, fftCoefficients)
        
    # Set labels for the graph
    plt.title(title) 
    plt.xlabel('Frequency [Hz]') 
    plt.ylabel('Amplitude')

    
def LoadSamples(filepath):
    # Load data into an array and return it
    return np.loadtxt( filepath )


def GenerateFIRCoefficientsBandStop(frequency1, frequency2, samplingFrequency, nTaps):
    # Normalise Frequencies and sclae to n taps
    k1 = int( (frequency1 / samplingFrequency ) * nTaps)
    k2 = int( (frequency2 / samplingFrequency ) * nTaps)

    # Define fft coefficients array values of 1 
    fftCoefficients = np.ones(nTaps)
    
    # Fitler unwanted frequencies by setting coeffients to zero at appropriate index values
    # 50Hz Hum
    fftCoefficients[ k1 : k2+1 ] = 0
    fftCoefficients[ nTaps-k2 : nTaps-k1 + 1 ] = 0
    # DC
    DCResolution = 2
    fftCoefficients[0 : DCResolution] = 0
    fftCoefficients[( (nTaps-1) - DCResolution ) : nTaps] = 0
    
    # Plot the frequency response of the filter
    PlotFrequency("FFT Coefficients - Filter", samplingFrequency, fftCoefficients)
    
    # Perform inverse Fourier transform
    ifftCoefficients = np.fft.ifft(fftCoefficients)
    ifftCoefficients = np.real(ifftCoefficients)
    
    # Swap the +ve and -ve time around M/2 
    impulseResponse = np.zeros(nTaps)
    impulseResponse[ 0 : int(nTaps/2) ] = ifftCoefficients[ int(nTaps/2) : nTaps ]
    impulseResponse[ int(nTaps/2) : nTaps ] = ifftCoefficients[ 0 : int(nTaps/2) ]
    
    # Create window function and multiply the coffecients by function to improve filter's performance
    filterCoefficients = impulseResponse * np.hanning(nTaps)
    
    # Plot Impulse Response & Windowed Impulse Response 
    PlotECGWaveforms('Filter Impulse Response(Bottom *Windowed', impulseResponse, filterCoefficients)

    return filterCoefficients    

if __name__ == "__main__":
    
    # Load Samples form .dat file and define sampling parameters 
    samples = LoadSamples("shortecg.dat")
    samplingFrequency = 250
    nSamples = len(samples)
    filteredSmaples = np.zeros(nSamples)
    
    # Calculate FFT coefficients of ECG signal
    ecgSpectrum = np.fft.fft(samples)
    ecgSpectrum = abs(ecgSpectrum)
    # Display frequency spectrum of unfiltered ECG Signal
    PlotFrequency('Unfiltered ECG - Frequency Spectrum', samplingFrequency, ecgSpectrum)
    
    # Calculate FIR filter coefficients
    firCoefficients = GenerateFIRCoefficientsBandStop(45,55, samplingFrequency, (2*samplingFrequency))
    
    # Initialize FIR object
    fir = fir_filter.FIR_filter(firCoefficients)
    
    # Simulate causal system by filtering signal sample by sample 
    for x in range(nSamples):
        filteredSmaples[x] = fir.dofilter(samples[x])
         
    # Plot original & filtered Signal 
    PlotECGWaveforms('ECG Signal (Bottom is Filtered)', samples, filteredSmaples)
    
    # Calculate FFT coefficients of filtered ECG signal
    ecgSpectrum = np.fft.fft(filteredSmaples)
    ecgSpectrum = abs(ecgSpectrum)
    PlotFrequency('Filtered ECG - Frequency Spectrum', samplingFrequency, ecgSpectrum)
    
    # Take a slice of ecg to compare
    unfilteredSlice = samples[860:1005]
    template = filteredSmaples[860:1005]
    PlotECGWaveforms('ECG Slice (Bottom is Filtered)', unfilteredSlice, template)
    
    # Display the graphs
    plt.show()
    
    # Create a Template for hr_detect.py
    # Scale to max value
    scailing = max(filteredSmaples)
    filteredSmaples *= (1/scailing)
    # Flip the slice 
    template = np.flip(template)
    # Display Template
    PlotWaveform('Template for hr_detect.py',template)
    np.savetxt('template.txt', np.c_[template])
    