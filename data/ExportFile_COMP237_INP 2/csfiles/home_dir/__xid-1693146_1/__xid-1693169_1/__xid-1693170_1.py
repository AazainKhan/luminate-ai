# -*- coding: utf-8 -*-
"""
Created on Mon Aug 17 10:59:14 2020

@author: mhabayeb
"""

import numpy as np
import matplotlib.pyplot as plt
import neurolab as nl
import os
path = "C:/Users/mhabayeb/Documents/COMP237_Data/"
filename = 'data_perceptron.txt'
fullpath = os.path.join(path,filename) 
"""
Load the data using the numpy loadtxt function

"""
text = np.loadtxt(fullpath)
# separate the data x1,x2 from the labels
data = text[:, :2]
#separate the labels
labels = text[:, 2]
labels = text[:, 2].reshape((text.shape[0], 1))
# Plot input data
plt.figure()
plt.scatter(data[:,0], data[:,1])
plt.xlabel('Dimension 1')
plt.ylabel('Dimension 2')
plt.title('Input data')
dim1_min, dim1_max, dim2_min, dim2_max = 0, 1, 0, 1
num_output = labels.shape[1]


# Define a perceptron with 2 input neurons (because we 
# have 2 dimensions in the input data)
dim1 = [dim1_min, dim1_max]
dim2 = [dim2_min, dim2_max]
perceptron = nl.net.newp([dim1, dim2], num_output)
#Train the network
error_progress = perceptron.train(data, labels, epochs=100, show=20, lr=0.03)
#Plot
# Plot the training progress
plt.figure()
plt.plot(error_progress)
plt.xlabel('Number of epochs')
plt.ylabel('Training error')
plt.title('Training error progress')
plt.grid()
plt.show()
