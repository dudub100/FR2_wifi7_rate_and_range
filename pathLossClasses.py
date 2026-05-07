# -*- coding: utf-8 -*-
"""
Created on Tue Mar 14 14:13:51 2023

@author: dudub
"""
import numpy

class Radio:
    
    def __init__(self,chBW=28, modulation="1024QAM", txPower=15, noiseFigure=5, alpha=0.125, codingRate = 0.94, pilots = 40):
        self.chBW = chBW
        self.modulation = modulation
        self.txPower = txPower
        self.noiseFigure = noiseFigure
        self.alpha=alpha
        self.codingRate = codingRate
        self.pilots = pilots
        
        
        # Create a dictionary of QAM and MSE to be used in receive level threshold calculations
        qamToMse = {"QPSK" : 9 ,
            "8QAM" : 12 ,
            "16QAM" : 15 ,
            "32QAM" : 18 , 
            "64QAM" : 21 ,
            "128QAM" : 24 ,
            "256QAM" : 27 ,
            "512QAM" : 30 ,
            "1024QAM" : 33 ,
            "2048QAM" : 36 ,
            "4096QAM" : 39 , 
            "8192QAM" : 42 ,
            "16384QAM" : 45 }
        qamToBit = {"QPSK" : 2 ,
            "8QAM" : 3 ,
            "16QAM" : 4 ,
            "32QAM" : 5 , 
            "64QAM" : 6 ,
            "128QAM" : 7 ,
            "256QAM" : 8 ,
            "512QAM" : 9 ,
            "1024QAM" : 10 ,
            "2048QAM" : 11 ,
            "4096QAM" : 12 , 
            "8192QAM" : 13 ,
            "16384QAM" : 14 }
        self.qamToMse = qamToMse
        self.qamToBit = qamToBit
        
    def __str__(self):
        return f"Radio with chBW {self.chBW} and modulation {self.modulation}"
    
    def mse(self):
        return self.qamToMse[self.modulation]
    def bit(self):
        return self.qamToBit[self.modulation]
    def capacity(self):
        return self.chBW / (1+self.alpha) * self.bit() * self.codingRate* (self.pilots-1)/self.pilots
    def thresholdRsl(self):
        noise = -114 + 10 * numpy.log10(self.chBW/(1+self.alpha)) + self.noiseFigure
        return noise+self.mse()
    def systemGain(self):
        return self.txPower - self.thresholdRsl()
                
 
class Antenna:
    def __init__(self,diameter = 1, frequency = 18):
        self.diameter = diameter
        self.frequency = frequency
        
        
    def __str__(self):
        return f"Antenns with diameter {self.diameter} feet at {self.frequency} GHz"

    def gain(self):
        lambda1 = 300e6 / (self.frequency * 1e9)
        area = numpy.pi*(self.diameter*0.305/2)**2
        return 10*numpy.log10(4*numpy.pi*0.55*area/(lambda1**2))
    
    def beamWidth(self):
        lambda1 = 300e6 / (self.frequency * 1e9)
        return 70 * lambda1 / (self.diameter * 0.305)
        
                                 
class Link:
    def __init__(self, rainZone = "K", frequency = 81, distance = 1, availability = 99.99, temperature = 15, polarization = 90, elevation = 0, waterVaporDensity = 7.5):
        self.rainZone = rainZone
        self.frequency = frequency
        self.distance = distance
        self.availability = availability
        self.temperature = temperature
        self.rainRate001 = {"A" : 8 , "B" : 12, "C" : 15 , "D" : 19 , "E" : 22 , "F" : 28 , "G" : 30 , "H" : 32 , "J" : 35 , "K" : 42 , "D2 (Crane)": 49, "L" : 60 , "M" : 63 , "N" : 95 , "P" : 145 , "Q" : 115}
        self.polarization = polarization
        self.elevation = elevation
        self.waterVaporDensity = waterVaporDensity

        
    def __str__(self):
        return f"{self.distance}Km Link in rain zone {self.rainZone} at {self.frequency} GHz "
    
    def freeSpaceLoss(self):
        return 92.5 + 20 * numpy.log10(self.frequency) + 20.0 * numpy.log10(self.distance)
    
    def atmosphericLoss(self):
        #Based on ITU-R P676-3 (1995)
        
        rp=1
        rt = 288/(273+self.temperature)
        #waterVaporDensity = 7.5
                               
        #Oxigen attenuation
        if self.frequency < 57:
            g1 = 7.27 * rt /(self.frequency**2+0.351*rp**2*rt**2)
            g2 = 7.5 / ((self.frequency-57)**2+2.44*rp**2*rt**2)
            g3 = self.frequency**2*rp**2*rt**2*1e-3
            gammaOxigen = (g1+g2)*g3
            
        elif self.frequency > 63:
            g1 = 2e-4 * rt**1.5*(1-1.2e-5*self.frequency**1.5)
            g2 = 4 / ((self.frequency-63)**2+1.5*rp**2*rt**2)
            g3 = 0.28*rt**2 / ((self.frequency-118.75)**2+2.84*rp**2*rt**2)
            g4 = self.frequency**2*rp**2*rt**2*1e-3
            gammaOxigen = (g1+g2+g3)*g4
                        
        else:
            g1 = 7.27 * rt /(57**2+0.351*rp**2*rt**2)
            g2 = 7.5 / ((57-57)**2+2.44*rp**2*rt**2)
            g3 = 57**2*rp**2*rt**2*1e-3
            gammaOxigen57 = (g1+g2)*g3
            
            g1 = 2e-4 * rt**1.5*(1-1.2e-5*63**1.5)
            g2 = 4 / ((63-63)**2+1.5*rp**2*rt**2)
            g3 = 0.28*rt**2 / ((63-118.75)**2+2.84*rp**2*rt**2)
            g4 = 63**2*rp**2*rt**2*1e-3
            gammaOxigen63 = (g1+g2+g3)*g4
            
            g1 = (self.frequency-60)*(self.frequency-63)*gammaOxigen57/18
            g2 = -1.66*rp**2*rt**8.5*(self.frequency-57)*(self.frequency-63)
            g3 = (self.frequency-57)*(self.frequency-60)*gammaOxigen63/18
            
            gammaOxigen = g1+g2+g3
            
        #print("----Oxigen")           
        #print(gammaOxigen)
        #Water attenuation
        t1 = 3.27e-2*rt + 1.67e-3 * self.waterVaporDensity *rt**7/rp + 7.7e-4*self.frequency**0.5
        t2 = 3.79 / ((self.frequency - 22.235)**2 + 9.81*rp**2*rt)
        t3 = 11.73*rt / ((self.frequency - 183.31)**2 + 11.81*rp**2*rt)
        t4 = 4.01*rt / ((self.frequency - 325.153)**2 + 10.44*rp**2*rt)
        t5 = self.frequency**2*self.waterVaporDensity*rp*rt*1e-4
        gammaWater = (t1+t2+t3+t4)*t5
        
        #print("----Water")           
        #print(gammaWater)
        return (gammaOxigen + gammaWater) * self.distance
        
    def rainLoss(self):
        #Based on ITU-R P.530-16 (2017)
        
        loss = {"V" : 0.0, "H" : 0.0}
        #d0 = 35 * numpy.exp(-0.015 * self.rainRate001[self.rainZone])

        paramKv = [[-3.80595,0.56934,0.81061],
            [-3.44965,-0.22911,0.51059],
            [-0.39902,0.73042,0.11899],
            [0.50167,1.07319,0.27195]]
        paramKv2 = [-0.16398,0.63297]
        
        paramAv = [[-0.07771,2.3384,-0.76284],
            [0.56727,0.95545,0.54039],
            [-0.20238,1.1452,0.26809],
            [-48.2991,0.791669,0.116226],
            [48.5833,0.791459,0.116479]]
        paramAv2 = [-0.053739,0.83433]
        
        paramKh = [[-5.3398,-0.10008,1.13098],
            [-0.35351,1.2697,0.454],
            [-0.23789,0.86036,0.15354],
            [-0.94158,0.64552,0.16817]]
        paramKh2 = [-0.18961,0.71147]

        paramAh = [[-0.14318,1.82442,-0.55187],
            [0.29591,0.77564,0.19822],
            [0.32177,0.63773,0.13164],
            [-5.3761,-0.9623,1.47828],
            [16.1721,-3.2998,3.4399]]
        paramAh2 = [0.67849,-1.95537]
        
        kh = 0.0
        for ind in range(0,4):
            a1 = numpy.log10(self.frequency) - paramKh[ind][1]
            a2 = a1 / paramKh[ind][2]
            a3 = a2**2
            a4 = numpy.exp(-a3)
            kh = kh + paramKh[ind][0] * a4
            
        kh = kh + paramKh2[0] * numpy.log10(self.frequency) + paramKh2[1]
        kh = 10**kh

        kv = 0.0
        for ind in range(0,4):
            a1 = numpy.log10(self.frequency) - paramKv[ind][1]
            a2 = a1 / paramKv[ind][2]
            a3 = a2**2
            a4 = numpy.exp(-a3)
            kv = kv + paramKv[ind][0] * a4
 
        kv = kv + paramKv2[0] * numpy.log10(self.frequency) + paramKv2[1]
        kv = 10**kv
        
        alphah = 0.0
        for ind in range(0,5):
            a1 = numpy.log10(self.frequency) - paramAh[ind][1]
            a2 = a1 / paramAh[ind][2]
            a3 = a2**2
            a4 = numpy.exp(-a3)
            alphah = alphah + paramAh[ind][0] * a4
            
        alphah = alphah + paramAh2[0] * numpy.log10(self.frequency) + paramAh2[1]


        alphav = 0.0
        for ind in range(0,5):
            a1 = numpy.log10(self.frequency) - paramAv[ind][1]
            a2 = a1 / paramAv[ind][2]
            a3 = a2**2
            a4 = numpy.exp(-a3)
            alphav = alphav + paramAv[ind][0] * a4
            
        alphav = alphav + paramAv2[0] * numpy.log10(self.frequency) + paramAv2[1]
        
        k = ((kh+kv) + (kh - kv)*numpy.cos(self.elevation*numpy.pi/180)**2*numpy.cos(2*self.polarization*numpy.pi/180))/2
        alpha = ((kh * alphah + kv * alphav) + (kh * alphah - kv * alphav)*numpy.cos(self.elevation*numpy.pi/180)**2*numpy.cos(2*self.polarization*numpy.pi/180))/(2*k)
        
        gamma = k * self.rainRate001[self.rainZone]**alpha
        
        #print("------")
        #print(kh)
        #print(kv)
        #print(alphah)
        #print(alphav)
        #print(k)
        #print(alpha)
        #print(gamma)
        #print(self.availability)
        #print("------)")
    
    
    
        invAvailability = 100.0 - self.availability
        
        r = (0.477 * self.distance**0.633 * self.rainRate001[self.rainZone]**(0.073*alpha)*self.frequency**0.123-10.579*(1-numpy.exp(-0.024*self.distance)))**-1
        r = min(r,2.5)
        effectiveDistance = self.distance * r
        
        c0 = 0.12 + 0.4*numpy.log10((self.frequency/10)**0.8)
        if self.frequency < 10:
            c0 = 0.12
        
        c1 = (0.07**c0)*(0.12**(1-c0))
        c2 = (0.855*c0)+(0.546*(1-c0))
        c3 = (0.139*c0)+(0.043*(1-c0))
        Ap = c1 * invAvailability**(-(c2+c3*numpy.log10(invAvailability)))
        rainLoss = gamma * Ap * effectiveDistance
        return rainLoss

        
      

        
        
        
        

