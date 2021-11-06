# -*- coding: utf-8 -*-
"""
Created on Wed Oct 21 09:09:47 2020

@author: Kamil

Dependecies:
    pip install ecg_gudb_database
    pip3 install ecg_gudb_database

"""

import numpy as np
from matplotlib import pyplot as plt
import fir_filter
from ecg_gudb_database import GUDb
  

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
    
    
def PlotFrequency(title, samplingFrequency, fftFrames):
    plt.figure()
    # Scale x-axis to sampling frequency 
    frequencyAxis   = np.linspace(0, samplingFrequency, len(fftFrames) )

    # Plot Frequency spectrum
    plt.plot( frequencyAxis, fftFrames) 
        
    # Set labels for the graph
    plt.title(title) 
    plt.xlabel('Frequency [Hz]') 
    plt.ylabel('Amplitude')
  
    
def LoadSamples(filepath):
    # Load data into an array and return it
    return np.loadtxt( filepath )

def GenerateFIRCoefficientsBandStop(frequency1, frequency2, samplingFrequency, nTaps):
    # Normalise Frequencies and sclae to m taps
    k1 = int( (frequency1 / samplingFrequency ) * nTaps)
    k2 = int( (frequency2 / samplingFrequency ) * nTaps)
    
    # Normalise 1.5hz Frequency and sclae to n taps
    dcK1 = int( (1.5 / samplingFrequency ) * nTaps)
    dcK2 = int( ((samplingFrequency-1.5) / samplingFrequency ) * nTaps)
    #print('dck1: ' + str(dcK1))
    #print('dcK2: ' + str(dcK2))

    # Define fft coefficients array values of 1 
    fftCoefficients = np.ones(nTaps)
    
    # Fitler unwanted frequencies by setting coeffients to zero at appropriate index values
    # 50Hz Hum
    fftCoefficients[ k1 : k2+1 ] = 0
    fftCoefficients[ nTaps-k2 : nTaps-k1 + 1 ] = 0
    # DC
    fftCoefficients[0:dcK1] = 0
    fftCoefficients[dcK2:nTaps] = 0
    
    # Plot Frequency response of the filter
    PlotFrequency("FFT Coefficients - Filter", samplingFrequency, fftCoefficients)
    
    # Perform inverse Fourier transform
    ifftCoefficients = np.fft.ifft(fftCoefficients)
    ifftCoefficients = np.real(ifftCoefficients)
    
    # Swap the +ve and -ve time around M/2 
    impulseResponse = np.zeros(nTaps)
    impulseResponse[ 0 : int(nTaps/2) ] = ifftCoefficients[ int(nTaps/2) : nTaps ]
    impulseResponse[ int(nTaps/2) : nTaps ] = ifftCoefficients[ 0 : int(nTaps/2) ]
    
    # Create window function and multiply the coffecients to improve filter's performance
    filterCoefficients = impulseResponse * np.hanning(nTaps)
    
    # Plot Windowed 
    PlotECGWaveforms('Filter Impulse Response (Bottom is *Windowed)', impulseResponse, filterCoefficients) 
    
    return filterCoefficients  


def GenerateECGTemplate(samples, samplingFrequency):
    filteredSmaples = []
    
    # Create Filter for the ECG
    firCoefficients = GenerateFIRCoefficientsBandStop(45,55, samplingFrequency, (2*samplingFrequency))
    
    # Initialize FIR 
    fir = fir_filter.FIR_filter(firCoefficients)
    
    # Filter first 1000 samples, enough to get the template
    for x in range(1000):
        filteredSmaples.append(fir.dofilter(samples[x])) 
           
    # Plot Filtered ECG
    PlotWaveform("Filtered ECG", filteredSmaples)
        
    # Get one Period of ECG
    ecgSlice = filteredSmaples[760:870] # [760:870]
    # Flip to create filter coefficients 
    template = np.flip(ecgSlice)
    
    # Plot both of ECG slices 
    PlotECGWaveforms('ECG Slice (Bottom is Template)', ecgSlice, template) 
    
    # reset FIR filter's ringbuffer and offset
    fir.ResetFilter()
    
    # Return the filter object and template coefficients 
    return fir, template
        
if __name__ == "__main__":
    
    # Handle optional arguments
    import argparse
    # Create argument parser object
    parser = argparse.ArgumentParser()
    # Create optional arguments
    parser.add_argument('--shortecg', default=False, action='store_true')
    # Create a namespace for the optional arguments
    args = parser.parse_args()
    
    templateFromShortECG = LoadSamples('template.txt')
    useShortECGTemplate = False
    PlotWaveform("Template from Short ECG", templateFromShortECG)
    
    # Get data ECG from GU Database 
    ecgclass = GUDb(12 , 'walking')
    samples = ecgclass.einthoven_II
    nSamples = len(samples)
    samplingFrequency = 250
    
    # Calculate FFT coefficients of ECG signal
    ecgSpectrum = np.fft.fft(samples)
    ecgSpectrum = abs(ecgSpectrum)
    # Display frequency spectrum of unfiltered ECG Signal
    PlotFrequency('Unfiltered ECG - Frequency Spectrum', samplingFrequency, ecgSpectrum)
    
    # Generate template from filtered Einthoven II ECG signal & Get FIR filter object
    fir, templateFromEinthoven = GenerateECGTemplate(samples, samplingFrequency)
    
    # Initialize arrays for filter outputs
    filteredSmaples = np.zeros(nSamples)
    squaredSamples = np.zeros(nSamples)
    
    # Peak Detector & Heart rate tracking variables 
    # R-peak index array
    peakIndex = []
    # Momentary heart rate array
    p = []
    lastPeak = 0
    nPeaks = 0

    pulseSettlingSamplecCnt = 68 # This detects 220BPM i.e maximum see report for details
    peakFlag = False 
    
    # If optionally specified use of ecg 
    if (args.shortecg == True):
        print('Using Template from Short Filtered ECG(ecg_filter.py)')
        template = templateFromShortECG
        amplitudeThreshold = 0.9e-5
    else:
        print('Using Filtered Einthoven II Recording Slice as Template')
        template = templateFromEinthoven
        amplitudeThreshold = 0.3e-10
    
    # Initialize matched filter object
    Templatefir = fir_filter.FIR_filter(template)

    # Simulate causal system by filtering signal sample by sample
    # Firstly filter dc and 50hz hum and then use matched filter to get pulses
    for x in range(nSamples):
        # Remove DC & 50Hz
        filteredSmaples[x] = fir.dofilter(samples[x])
        # Apply matched filter 
        squaredSamples[x] = Templatefir.dofilter(filteredSmaples[x])
        # Square the result to reduce noise
        squaredSamples[x] = squaredSamples[x] * squaredSamples[x]
        
        # Wait for the filter to settle
        if(x > 500):
            
            # Detect Peaks 
            # If sample amplitude is above threshold, the peak hasn't been detected before and and 20 samples pasted since last peak
            if( squaredSamples[x] > amplitudeThreshold and peakFlag == False and (x - lastPeak ) >= pulseSettlingSamplecCnt ):
                # In the vicinity of the peak
                peakFlag = True
                
            # If the amplitude exceeded threshold and previous sample was higher that must've been the peak
            if( squaredSamples[x - 1] > squaredSamples[x] and peakFlag == True ):
                # Reset flag
                peakFlag = False 
                
                # Hold this index as last peak index 
                lastPeak = (x - 1)
                # Also append the index of that sample to list
                peakIndex.append( lastPeak )
                # Increment peak counter
                nPeaks += 1 
                
                # If there are enough peaks to determine momentary time
                if ( nPeaks >= 2):
                    # Calculate number of samples between peaks
                    t = lastPeak - peakIndex[ nPeaks - 2]
                    # Calculate momentary time and append it to the list
                    p.append( (samplingFrequency/t)*60 )
     
    
    # Calculate FFT coefficients of filtered ECG signal
    ecgSpectrum = np.fft.fft(filteredSmaples)
    ecgSpectrum = abs(ecgSpectrum)
    PlotFrequency('Filtered ECG - Frequency Spectrum', samplingFrequency, ecgSpectrum)
           
    PlotECGWaveforms('Original & Filtered Einthoven II walking ECG', samples, filteredSmaples)
    PlotWaveform("Delta Pulses from matched filtering", squaredSamples) 
    PlotWaveform("Momenrary Heart Rate", p)       
    
    roundedP = np.around(p, 1)
    
    print("Number of beats detected: " + str(nPeaks) )
    print("Peaks occur at index values: ")
    print(peakIndex)
    print("Number of Momentary Heart Rate calculated: " + str(len(p)))
    print("Momentary Heart Rate (in BPM): ")
    print(roundedP)
    print("Max Momentary Heart Rate (in BPM): %.1f" % max(p))
    print("Min Momentary Heart Rate (in BPM): %.1f" % min(p))
    
    # Display Graphs
    plt.show()


