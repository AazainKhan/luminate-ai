# -*- coding: utf-8 -*-
"""
Created on Mon Aug 17 20:11:54 2020

@author: mhabayeb
"""

import numpy as np
import matplotlib.pyplot as plt
import neurolab as nl
import os
path = "C:/Users/mhabayeb/Documents/COMP237_Data/"
filename = 'data_simple_nn.txt'
fullpath = os.path.join(path,filename) 
text = np.loadtxt(fullpath)
# separate the data
data = text[:, 0:2]
labels = text[:, 2:]
#Plot the data
# Plot input data
plt.figure()
plt.scatter(data[:,0], data[:,1])
plt.xlabel('Dimension 1')
plt.ylabel('Dimension 2')
plt.title('Input data')
# Minimum and maximum values for each dimension
dim1_min, dim1_max = data[:,0].min(), data[:,0].max()
dim2_min, dim2_max = data[:,1].min(), data[:,1].max()
# Define the number of neurons in the output layer shape[0] gives number of rows , shape[1] gives number of columns
num_output = labels.shape[1]
# Define a single-layer neural network
dim1 = [dim1_min, dim1_max]
dim2 = [dim2_min, dim2_max]
nn = nl.net.newp([dim1, dim2], num_output)
# Train the neural network
error_progress = nn.train(data, labels, epochs=1000, show=20, lr=0.003)
 #Plot the training progress
plt.figure()
plt.plot(error_progress)
plt.xlabel('Number of epochs')
plt.ylabel('Training error')
plt.title('Training error progress')
plt.grid()
plt.show()

# Run the classifier on test datapoints
print('\nTest results:')
data_test = [[0.4, 4.3], [4.4, 0.6], [4.7, 8.1], [0.9,7.4],[7,4],[4,7],[7.2,4.1]]
for item in data_test:
    print(item, '-->', nn.sim([item])[0])