# -*- coding: utf-8 -*-
"""
Konstantinos Trevlopoulos
Last update: 11.12.2020

This script implements the procedure described in the section "Convolution:
AF( f ) Dependent on Sra( f )" in Bazzurro and Cronell (2004).

https://pubs.geoscienceworld.org/ssa/bssa/article-abstract/94/6/2110/147012/
Nonlinear-Soil-Site-Effects-in-Probabilistic

The script initially reads the hazard curves in a .hdf5 file created by the
OpenQuane Engine. Then it computes the new hazard curves through convolution.

The versions of the pieces of software that were used:
Spyder 3.3.6, Python 3.7.4 - IPython 7.8.0, OpenQuane Engine version 3.10,
h5py 2.9.0, numpy 1.16.5, scipy 1.3.1, pandas 0.25.1, glob2 0.7
"""

import h5py
import numpy as np
import pandas as pd
import glob
from resp_spec import *
from scipy.stats import norm
from scipy.optimize import curve_fit

# Enter the path to the .hdf5 file
path2files='C:\\Users\\user1\\oqdata\\'
# Enter the filename of the .hdf5 file created by the Classical PSHA
hdf5FileName = 'calc_20201211.hdf5'
file2read = path2files+hdf5FileName
f = h5py.File(file2read, "r")



#%%  
# Get the intensity measure levels for the hazard curves
oqparamDFrame = pd.DataFrame( data = f['oqparam'][:] )
oqparam_name = list()
for m in range(len(oqparamDFrame)):
    oqparam_name.append(oqparamDFrame.iloc[m][0].decode('UTF-8'))
oqparam_value = list()
for m in range(len(oqparamDFrame)):
    oqparam_value.append(oqparamDFrame.iloc[m][1].decode('UTF-8'))



periods4hazCurves = list()
for j in oqparam_name:
    if j == 'hazard_imtls.PGA':
        periods4hazCurves.append(0)
    if j[0:15] == 'hazard_imtls.SA':
        pos1 = oqparam_name[9].find('(')
        pos2 = oqparam_name[9].find(')')
        periods4hazCurves.append(float(j[j.find('(')+1:j.find(')')]))
freq4hazCurves = list()
for j in periods4hazCurves:
    # We assume that PSA(100 Hz) = PSA(0 s)
    if j == 0:
        freq4hazCurves.append(100)
    else:
        freq4hazCurves.append(1/j)
#freq4hazCurves.reverse(periods4hazCurves)
        
        
# In order to generate a .csv file which can be used to apply the convolution
# using the OpenQuake Engine, make sure that the intensity levels for all
# intensity measures in the PSHA are the same. This needs to be done because
# each line in the .csv file has the same intensity level for all intensity
# measures. Luckily, this was done in the PSHA that generated the .hdf5 file,
# which is used in this example
imLevels4hazCurves = list()
for j in range(len(oqparam_name)):
    if oqparam_name[j][0:12] == 'hazard_imtls':
        imLevels4hazCurves.append(np.fromstring(oqparam_value[j][
                oqparam_value[j].find('[')+1:
                    oqparam_value[j].find(']')], sep=','))


    
#%%    
# Get the exceedance probabilities for the hazard curves
tempHcurve = f['hcurves-stats'][:]
exProb4hazCurves = list()
#pos1=0
#for j in range(len(periods4hazCurves)):
#    exProb4hazCurves.append( tempHcurve[0][0][
#            pos1:pos1+len(imLevels4hazCurves[j])] )
#    pos1 += len(imLevels4hazCurves[j])
for j in range(len(periods4hazCurves)):
    exProb4hazCurves.append( tempHcurve[0][0][j] )


#%%  
# Read the acceleration time-histories at the rock outcrop (input) and at the
# surface of the ground (output), and compute their response spectra

# Enter the folder where the files with the time-histories are found.
# Put all those files in this folder
path2accTHist = 'C:\\Users\\user1\\site_response_analysis'


# The filenames of the input time-histories.
# ATTENTION:
# In this example, the files were generated by STRATA and each file contains
# one time-history.
# Edit the searched filenames as needed.
fileNamesAccInp = glob.glob(path2accTHist+'\\*Bedrock*accelTs*')
timeHistorInp = list()
for j in fileNamesAccInp:
    timeHistorInp.append(np.genfromtxt(j,delimiter=',', skip_header=3))
# Dito
fileNamesAccOut = glob.glob(path2accTHist+'\\*0.00*accelTs*')
timeHistorOut = list()
for j in fileNamesAccOut:
    timeHistorOut.append(np.genfromtxt(j,delimiter=',', skip_header=3))
    
    
    
# ATTENTION:
# The code that computes the response spectra assumes that each time-history
# has a constant time-step
damping = 0.05
respSpectraInp = list()
for j in timeHistorInp:
    timeStep = j[1,0] - j[0,0]
    temp = np.zeros(len(periods4hazCurves))
    temp[0] = max(abs(j[:,1]))
    PSA, PSV, SD = ins_resp(j[:,1], timeStep, periods4hazCurves[1:], damping)
    temp[1:] = PSA.copy()
    respSpectraInp.append( temp )
respSpectraOut = list()
for j in timeHistorOut:
    timeStep = j[1,0] - j[0,0]
    temp = np.zeros(len(periods4hazCurves))
    temp[0] = max(abs(j[:,1]))
    PSA, PSV, SD = ins_resp(j[:,1], timeStep, periods4hazCurves[1:], damping)
    temp[1:] = PSA.copy()
    respSpectraOut.append( temp )



#%%  
# Compute amplification (of the response spectra) for each ground motion
ampliFunPerGM = list()
for j in range(len(timeHistorInp)):
    ampliFunPerGM.append(
            np.array(respSpectraOut[j]) / np.array(respSpectraInp[j]))
# Compute amplification for each period  
ampliFun = list()
for j in range(len(periods4hazCurves)):
    ampliFun.append(np.zeros(len(timeHistorInp)))
    for m in range(len(timeHistorInp)):
        ampliFun[j][m] = ampliFunPerGM[m][j].copy()



#%%  
# Differentiate the rock-hazard curves.
# This is required in order to compute Equation 3. The paper says
# "The term pX(xj) represents the probability that the rockinput
# level is equal to (or better, in the neighborhood of ) xj.
# This term can be approximately derived by differentiating
# the rock-hazard curve in discrete or numerical form."
# However, the differentiation of a typical hazard curve gives negative values
# and negative values are not probabilities. On the other hand, the absolute
# of the result of the differentiation looks like a PDF. The pX(xj) in the
# paper is a function that looks like a PDF. Therefore, we are using the
# the absolute of the gradient of the hazard curve.
diffExProb4hazCurves = list()
for j in range(len(exProb4hazCurves)):
        diffExProb4hazCurves.append( np.absolute( np.gradient( exProb4hazCurves[j].copy(),
                            imLevels4hazCurves[j]) ) )



# Compute the function G_{Y|X}(z/x|x) in Equation 4
medians4oqe = np.zeros( (len(imLevels4hazCurves[0]), len(periods4hazCurves) ) )
dispersion4oqe = np.zeros( (len(imLevels4hazCurves[0]), len(periods4hazCurves) ) )
funGeq4 = list()
xValues = list()
for j in range(len(periods4hazCurves)):
    xValues.append( np.zeros(len(timeHistorInp)) )
    yValues = ampliFun[j]
    funGeq4.append(list())
    for n in range(len(timeHistorInp)):
        xValues[j][n] = respSpectraInp[n][j].copy()
    for m in range(len(imLevels4hazCurves[j])):
        dispersion = 0;
        # The thresholds, i.e. the amplification ratios
        yThresholds = imLevels4hazCurves[j][m] / imLevels4hazCurves[j]
        p = np.polyfit(np.log(xValues[j]), np.log(yValues), 1);
        c = p[0].copy();
        lnb = p[1].copy();
        lnD = lnb.copy() + c.copy() * np.log(xValues[j].copy());
        epsilon = np.log(yValues.copy()) - lnD.copy();
        dispersion = np.std(epsilon.copy()) / abs(c.copy());
        b = np.exp( lnb.copy() );
        medians = np.exp( np.log( yThresholds.copy() / b.copy() ) / abs(c.copy()) );
        funGeq4[-1].append(norm.sf(np.log(imLevels4hazCurves[j][m].copy()),
               np.log(medians.copy()), dispersion.copy()))
        medians4oqe[m,j] = np.exp( lnb.copy() + c.copy() * np.log( imLevels4hazCurves[j][m].copy() ) )
        dispersion4oqe[m,j] = dispersion.copy()



#%%  
# Do the convolution to compute the new hazard curves
# This is the list containing the probabilities for the new hazard curves
exProb4hazCurvesNew = list()
for j in range(len(periods4hazCurves)):
    exProb4hazCurvesNew.append( np.zeros(len(imLevels4hazCurves[j])) )
    # The Equation 2 has dx in the integral, but there is no Delta\x at the end
    # of Equation 3. This term (deltaIM) needs to be at the end of the sum
    # (the discretized form of the integral) in Equation 3.
    deltaIM = np.zeros(len(imLevels4hazCurves[j]))
    # Reminder: we used 2nd order finite differences for the gradient
    deltaIM[0] = imLevels4hazCurves[j][1]-imLevels4hazCurves[j][0]
    deltaIM[-1] = imLevels4hazCurves[j][-1]-imLevels4hazCurves[j][-2]
    deltaIM[1:-1] = imLevels4hazCurves[j][2:]-imLevels4hazCurves[j][:-2]
    deltaIM = deltaIM.copy() / 2
    for m in range(len(imLevels4hazCurves[j])):
        exProb4hazCurvesNew[-1][m] = np.sum(
                (1-funGeq4[j][m].copy())*diffExProb4hazCurves[j].copy()*deltaIM.copy())



#%%
# Export the results in .csv files and make figures
# Work in progress...
import matplotlib.pyplot as plt
j = 0
#j = 6
plt.xlim(0.0001, 10)
plt.ylim(0.00001, 1)
#plt.plot(imLevels4hazCurves[j], exProb4hazCurves[j])
#plt.plot(imLevels4hazCurves[j], exProb4hazCurvesNew[j])
plt.loglog(imLevels4hazCurves[j], exProb4hazCurves[j])
plt.loglog(imLevels4hazCurves[j], exProb4hazCurvesNew[j])
plt.show()

#j = 0
#plt.plot(imLevels4hazCurves[j], exProb4hazCurvesNew[j])



#%%
# Generate a .csv file with the amplificaiton function
# which can be used to apply the convolution using the OpenQuake Engine


# The .csv file with the amplification
f1=open('amp4oqe.csv', 'a')

# The name of the site. There is one site in this example
siteName = 'TST'

# Reminder: the PSHA that generated the results was done for the same intensity
# measure levels for every intensity measure. That is why we can do this:
firstLineOfCSV = '#vs30_ref=800' + ','*(2*len( periods4hazCurves ) + 1)
f1.write(firstLineOfCSV + "\n");

secondLineOfCSV = 'ampcode,level,PGA'
for j in range( 1, len( periods4hazCurves ) ):
    secondLineOfCSV = secondLineOfCSV + ',SA(' + str(periods4hazCurves[j]) + ')';
secondLineOfCSV = secondLineOfCSV + ',sigma_PGA'
for j in range( 1, len( periods4hazCurves ) ):
    secondLineOfCSV = secondLineOfCSV + ',sigma_SA(' + str(periods4hazCurves[j]) + ')';
f1.write(secondLineOfCSV + "\n");

for j in range( len( imLevels4hazCurves[0] ) ):
    nextLineOfCSV = siteName + ',' + str(imLevels4hazCurves[0][j])
    for k in range( len( periods4hazCurves ) ):
        nextLineOfCSV = nextLineOfCSV + ',' + str(medians4oqe[j,k]);
    for k in range( len( periods4hazCurves ) ):
        nextLineOfCSV = nextLineOfCSV + ',' + str(dispersion4oqe[j,k]);
    f1.write(nextLineOfCSV + "\n");


f1.close()
