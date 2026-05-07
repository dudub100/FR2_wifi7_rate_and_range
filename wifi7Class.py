import numpy

class wifi7Radio:
    
    def __init__(self,chBW=320, mcs=13, txPower=15, noiseFigure=5, guardInterval = 1.6):
        self.chBW = chBW
        self.mcs = mcs
        self.txPower = txPower
        self.noiseFigure = noiseFigure
        self.guardInterval = guardInterval
        self.symbolTime = 12.8
        
        
        # Create a dictionary of QAM and MSE to be used in receive level threshold calculations
        
        bwToTones = { 20:234,
        40:468,
        60:746,
        80:980,
        140:1726,
        160:1960,
        320:3920}
        
        mcsToCoding = { 0: [1, 1/2,2],
        1:[2, 1/2,5],
        2:[2,3/4,8],
        3:[4,1/2,11],
        4:[4,3/4,14],
        5:[6,2/3,16],
        6:[6,3/4,18 ],
        7:[6,5/6,21],
        8:[8,3/4,24],
        9:[8,5/6,27],
        10:[10,3/4,30],
        11:[10,5/6,33],
        12:[12,3/4,36],
        13:[12,5/6,39]}
        
        self.bwToTones = bwToTones
        self.mcsToCoding = mcsToCoding
        
        
        
    def __str__(self):
        return f"Wifi7 Radio with chBW {self.chBW} and mcs {self.mcs}"
    
    def mse(self):
        return self.mcsToCoding[self.mcs][2]
    def bit(self):
        return self.mcsToCoding[self.mcs][0]
    def capacity(self):
    	
        tones = self.bwToTones[self.chBW]
        codingRate = self.mcsToCoding[self.mcs][1]
        bits = self.mcsToCoding[self.mcs][0]
        
        return tones * bits * codingRate / (self.symbolTime + self.guardInterval)
        
    def thresholdRsl(self):
        noise = -114 + 10 * numpy.log10(self.chBW) + self.noiseFigure
        return noise+self.mse()
    def systemGain(self):
        return self.txPower - self.thresholdRsl()
                
