# -*- coding: utf-8 -*-
"""
Created on Wed Oct 21 09:10:11 2020

@author: Kamil
"""

import numpy as np

class FIR_filter:

    def __init__( self, _coefficients ):
        self.coeffFIR = _coefficients
        self.nTaps = len(_coefficients)
        self.ringbuffer = np.zeros(self.nTaps)
        self.ringBufferOffset = 0
    
    def dofilter( self, inputValue ):
        # Store new value at the offset 
        self.ringbuffer[self.ringBufferOffset] = inputValue
        
        # Set offset variables
        offset = self.ringBufferOffset
        coeffOffset = 0
        
        # Initialize output to zero
        output = 0
        
        # Multiply values with coefficients until it reaches the beginning of the ring buffer
        while( offset >= 0 ):
            # Calculate tap value and add it to a sum
            output += self.ringbuffer[offset] * self.coeffFIR[coeffOffset] 
            # Move offsets 
            offset -= 1
            coeffOffset += 1
    
        # Set the offset to end of the array 
        offset = self.nTaps - 1
        
        # Multiply coefficients until it reaches the start of the ring buffer
        while( self.ringBufferOffset < offset ):
            # Calculate tap value and add it to a sum
            output += self.ringbuffer[offset] * self.coeffFIR[coeffOffset] 
            # Move offsets 
            offset -= 1
            coeffOffset += 1
           
        # Check if the next inputValue would be placed outside of the boundary of ring buffer and prevent this by wraping to the index of first element
        if( (offset + 1) >= self.nTaps ):
            self.ringBufferOffset = 0
        # The next offset value doesn't exceed the boundary
        else:
            self.ringBufferOffset += 1
            
        return output
    
    
    def ResetFilter( self ):
        # Reset the current offset and clear ringbuffer 
        self.ringBufferOffset = 0
        self.ringbuffer = np.zeros(self.nTaps)
    
    
def unittest():
    # Define test sample vector, enough elements to test the wrap around
    testSamples = [1,2,3,4,5,6]
    nSample = 6
    # Define test FIR filter coefficients vector
    firCoefficients = [1,2,3,4,5]
    nFilterTaps = 5 
    
    # Define ring buffer expected vector
    expectedRingBufferItteration = [ [1,0,0,0,0],
                                    [1,2,0,0,0],
                                    [1,2,3,0,0],
                                    [1,2,3,4,0],
                                    [1,2,3,4,5],
                                    [6,2,3,4,5] ]

    expectedRingBufferOffset = [1, 2, 3, 4, 0, 1]
    
    # Define output for each sample processed in testsample vector
    expectedFilteroutput = [ 1, 4, 10, 20, 35, 50 ]

      
    print("INITLIALIZING FIR OBJECT!")
    # Initialize filter object
    fir = FIR_filter(firCoefficients)
    
    print("TESTING FIR FILTER!\n")
    if(fir.nTaps != nFilterTaps ):
        print("FIR FILTER IS BROKEN! - FILTER'S NUMBER OF TAPS IS INCORRECT!")
        return 
    
    for x in range(nSample):
        output = fir.dofilter(testSamples[x])
        
        # Verify output
        if (output != expectedFilteroutput[x]):
            print("FIR FILTER IS BROKEN! - FILTER OUTPUT IS INCORRECT!")
            print("Itteration Index: " + str(x) )
            print("Output: " + str(output) + " Expected: " + str(expectedFilteroutput[x]) )
            return 
        
        # Verify offset itterates correctly and witin boundaries
        if (fir.ringBufferOffset != expectedRingBufferOffset[x]):
            print("FIR FILTER IS BROKEN! - FILTER BUFFER OFFSET IS INCORRECT!")
            print("Itteration Index: " + str(x) )
            print("Output: " + str(fir.ringBufferOffset) + " Expected: " + str(expectedRingBufferOffset[x]) )
            return 
        
        # Verify contents of ring buffer  
        for i in range(nFilterTaps):
            if ( fir.ringbuffer[i] != expectedRingBufferItteration[x][i] ):
                print("FIR FILTER IS BROKEN! - FILTER BUFFER CONTENT IS INCORRECT!")
                print("Itteration Index: " + str(x) + " Element: " + str(i) )
                print("Output: " + str(fir.ringBufferOffset) + " Expected: " + str(expectedRingBufferOffset[x]) )
                return 
    
    print("\nFIR FILTER IS OPERATING CORRECTLY!")
    return
    
if __name__ == "__main__":
    
    unittest()
    
    """ 
    Numerical Explanation for the expected value
        
    (offset >= 0) - RESULT: 1.0 Ring Buffer Element = 1.0 Tap Value = 1
    (self.ringBufferOffset < offset) - RESULT: 0.0 Ring Buffer Element = 0.0 Tap Value = 2
    (self.ringBufferOffset < offset) - RESULT: 0.0 Ring Buffer Element = 0.0 Tap Value = 3
    (self.ringBufferOffset < offset) - RESULT: 0.0 Ring Buffer Element = 0.0 Tap Value = 4
    (self.ringBufferOffset < offset) - RESULT: 0.0 Ring Buffer Element = 0.0 Tap Value = 5
    Sum of products is: 1.0
    
    
    (offset >= 0) - RESULT: 2.0 Ring Buffer Element = 2.0 Tap Value = 1
    (offset >= 0) - RESULT: 2.0 Ring Buffer Element = 1.0 Tap Value = 2
    (self.ringBufferOffset < offset) - RESULT: 0.0 Ring Buffer Element = 0.0 Tap Value = 3
    (self.ringBufferOffset < offset) - RESULT: 0.0 Ring Buffer Element = 0.0 Tap Value = 4
    (self.ringBufferOffset < offset) - RESULT: 0.0 Ring Buffer Element = 0.0 Tap Value = 5
    Sum of products is: 4.0
    
    
    (offset >= 0) - RESULT: 3.0 Ring Buffer Element = 3.0 Tap Value = 1
    (offset >= 0) - RESULT: 4.0 Ring Buffer Element = 2.0 Tap Value = 2
    (offset >= 0) - RESULT: 3.0 Ring Buffer Element = 1.0 Tap Value = 3
    (self.ringBufferOffset < offset) - RESULT: 0.0 Ring Buffer Element = 0.0 Tap Value = 4
    (self.ringBufferOffset < offset) - RESULT: 0.0 Ring Buffer Element = 0.0 Tap Value = 5
    Sum of products is: 10.0
    
    
    (offset >= 0) - RESULT: 4.0 Ring Buffer Element = 4.0 Tap Value = 1
    (offset >= 0) - RESULT: 6.0 Ring Buffer Element = 3.0 Tap Value = 2
    (offset >= 0) - RESULT: 6.0 Ring Buffer Element = 2.0 Tap Value = 3
    (offset >= 0) - RESULT: 4.0 Ring Buffer Element = 1.0 Tap Value = 4
    (self.ringBufferOffset < offset) - RESULT: 0.0 Ring Buffer Element = 0.0 Tap Value = 5
    Sum of products is: 20.0
    
    
    (offset >= 0) - RESULT: 5.0 Ring Buffer Element = 5.0 Tap Value = 1
    (offset >= 0) - RESULT: 8.0 Ring Buffer Element = 4.0 Tap Value = 2
    (offset >= 0) - RESULT: 9.0 Ring Buffer Element = 3.0 Tap Value = 3
    (offset >= 0) - RESULT: 8.0 Ring Buffer Element = 2.0 Tap Value = 4
    (offset >= 0) - RESULT: 5.0 Ring Buffer Element = 1.0 Tap Value = 5
    Sum of products is: 35.0
    
    
    (offset >= 0) - RESULT: 6.0 Ring Buffer Element = 6.0 Tap Value = 1
    (self.ringBufferOffset < offset) - RESULT: 10.0 Ring Buffer Element = 5.0 Tap Value = 2
    (self.ringBufferOffset < offset) - RESULT: 12.0 Ring Buffer Element = 4.0 Tap Value = 3
    (self.ringBufferOffset < offset) - RESULT: 12.0 Ring Buffer Element = 3.0 Tap Value = 4
    (self.ringBufferOffset < offset) - RESULT: 10.0 Ring Buffer Element = 2.0 Tap Value = 5
    Sum of products is: 50.0 
     """      
    