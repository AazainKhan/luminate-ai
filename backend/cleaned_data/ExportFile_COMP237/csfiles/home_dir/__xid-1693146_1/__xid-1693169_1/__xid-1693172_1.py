# -*- coding: utf-8 -*-
"""
Created on Mon Aug 17 22:40:41 2020
Neural network with continous input and continous output
"""
import numpy as np
import matplotlib.pyplot as plt
import neurolab as nl
min_val = -15
max_val = 15
num_points = 130
x = np.linspace(min_val, max_val, num_points)

y = 3 * np.square(x) + 5
y /= np.linalg.norm(y)
# Create data and labels
print(np.shape(x))
data = x.reshape(num_points, 1)
labels = y.reshape(num_points, 1)
# Plot input data
plt.figure()
plt.scatter(data, labels)
plt.xlabel('Dimension 1')
plt.ylabel('Dimension 2')
plt.title('Input data')
# Define a multilayer neural network with 2 hidden layers;
# First hidden layer consists of 10 neurons
# Second hidden layer consists of 6 neurons
# Output layer consists of 1 neuron
nn = nl.net.newff([[min_val, max_val]], [10, 6, 1])
# Set the training algorithm to gradient descent
nn.trainf = nl.train.train_gd
# Train the neural network
error_progress = nn.train(data, labels, epochs=2000, show=100, goal=0.01)
# Plot training error
plt.figure() 
plt.plot(error_progress)
plt.xlabel('Number of epochs')
plt.ylabel('Error')
plt.title('Training error progress')
#use the same data 
output = nn.sim(data)
y_pred = output.reshape(num_points)
plt.figure()
plt.plot( x, y_pred, 'b')
plt.title('Actual vs predicted')
plt.show()
#####
plt.figure()
plt.plot(x, y_pred, 'r', x, y, '.', x, y, 'b')
plt.title('Actual vs predicted')
plt.show()


