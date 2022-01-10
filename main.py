__author__ = "John Jack Messerly"

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import utils
arr = np.asarray

"""
run to see some quick insights
"""
if __name__== '__main__':
  path_file = 'path.csv'
  tracker_file = 'tracker.csv'
  merged_file = 'merged.csv'
  merged = utils.merge_trajectories(path_file,tracker_file,merged_file,verbose=True)

  # separate into numpy arrays for plotting 
  path = arr(merged[['x_pth','y_pth']])
  tracker = arr(merged[['x_trk','y_trk']])
 
  # run validation
  T,A,b,r2 = utils.fit_transformation(tracker,path) 
  utils.fit_validation(merged,epochs=500)

  # plot all samples
  utils.plot_samples(tracker,path,'raw data')

  # show some speed 
  utils.show_speed(merged[0:3000],'x_pth','y_pth','planner segment velocity 0.1s intervals')

