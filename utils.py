__author__ = "John Jack Messerly"

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn import linear_model
import time, os
arr = np.asarray


"""
merge and sychronize csv files based on timestmaps

drops the z dimension
"""
def merge_trajectories(path_file,tracker_file,merged_file,time_delta='5m',verbose=False,save=True):
  start_time = time.time()
  
  # read and rename the path
  path_log = pd.read_csv(path_file,index_col=0)
  path_log = path_log.rename(columns={"t_pth":"t"})
  path_log = path_log.drop(['index','z_pth'],axis=1)
  path_log['t'] = pd.to_datetime(path_log['t'])

  track_log = pd.read_csv(tracker_file,index_col=0)
  track_log = track_log.rename(columns={"t_trk":"t"})
  track_log = track_log.drop(['index','z_trk'],axis=1)
  track_log['t'] = pd.to_datetime(track_log['t'])

  # synchronize timestamps with a dt = 5 milliseconds and nearest-neighbors 
  merged = pd.merge_asof(path_log,track_log,on='t',tolerance=pd.Timedelta(time_delta))

  # reorder columns so time is at the end
  merged = merged[['x_pth','y_pth','x_trk','y_trk','t']]

  # drop first and last few rows when there aren't good time line-ups
  before_dropping = merged.size
  merged = merged.dropna(axis=0,how='any')
  after_dropping = merged.size
  dropped = before_dropping - after_dropping

  # save to a new csv for inspection
  if save:
    merged.to_csv(merged_file)

  # log some info
  if verbose:
    print("merged size %d | Nans Dropped %d | process time %f" 
          % (merged.size,dropped,(time.time() - start_time)))
  return merged

"""
plot some path and tracker trajectories
"""
def plot_samples(path,tracker,title):
  fig, ax = plt.subplots()
  ax.scatter(path[:,0],path[:,1],c='tab:blue',label='path',edgecolors='none')
  ax.scatter(tracker[:,0],tracker[:,1],c='tab:orange',label='tracker',edgecolors='none')
  ax.legend()
  ax.grid(True)
  plt.title(title)
  plt.xlabel('x')
  plt.ylabel('y')
  plt.show()

"""
decompose a 2D homogeneous transformation matrix T into its
rotation, translation, scaling and shear
"""
def decompose_transformation(T):
  trans = np.eye(3)
  trans[0:2,2] = T[0:2,2]
  T[0:2,2] = [0,0]

  # split into unitary and upper diagonal
  Q,R = np.linalg.qr(T)
  
  refl = np.eye(3)
  # detect a reflection
  if np.linalg.det(Q) < 0:
    refl[1,1] = -1

  # find the rotation
  rot = np.matmul(refl,Q)

  # find the scaling
  scale = np.eye(3)
  scale[0,0] = R[0,0]
  scale[1,1] = R[1,1]

  # simple algebra to isolate shear from the upper diagonal
  shear = np.matmul(R,np.linalg.inv(scale))

  return [trans,refl,rot,shear,scale] 
 
"""
find a 2D homography between the tracker and path using 
random consensus and least-squares
"""
def fit_transformation(tracker,path,verbose=False):
  start_time = time.time()

  # least-squares regression
  reg = linear_model.LinearRegression()
  reg.fit(tracker,path)
  A = reg.coef_
  b = reg.intercept_

  # log some info
  if verbose:
    print('fit with %d samples | R^2 %f | total time %f' % 
    (merged.size, reg.score(tracker,path),time.time() - start_time))

  # convert to pose matrix
  T = np.eye(3)
  T[0:2,0:2] = A
  T[0:2,2] = b
  return T, A, b, reg.score(tracker,path)



"""
algorithm for sanity checking the 2D transformation

runs "epoch" many experiments
each experiment uses a random subset of the data equal to (Total Samples / batch_div)
statistics for each transformation type computed separately

"""
def fit_validation(merged,epochs=100,batch_div = 10):
  start_time = time.time()
  total_samples = merged.size
  batch_size = int(total_samples / batch_div)
  merged = merged.to_numpy(dtype=np.float64)

  """
  lists of statistics to track separately
  """
  transx = list()
  transy = list()
  refls = list()
  rots = list()
  scalingx = list()
  scalingy = list()
  shearx = list()
  r2s = list()

  """
  fit with many random subsamples to validate good fit
  """
  for epoch in range(epochs):
    # make a new random batch
    merged_shuffle = np.random.permutation(merged)[0:batch_size]
    path_samples = merged_shuffle[:,[0,1]]
    tracker_samples = merged_shuffle[:,[2,3]]

    # fit the data
    T,A,b,r2 = fit_transformation(tracker_samples,path_samples)
    T = decompose_transformation(T)
    
    # fill in stats
    transx.append(T[0][0,2])
    transy.append(T[0][1,2])
    
    rot_mat = T[2]
    theta = np.arctan2(rot_mat[0,1],rot_mat[0,0])
    rots.append(theta) 
  
    refls.append(T[1][1,1])

    scalingx.append(T[4][0,0])
    scalingy.append(T[4][1,1])

    shearx.append(T[3][0,1])

    r2s.append(r2)

  print('experiments run: %d in %f seconds' % (epochs,time.time() - start_time))
  print('experiment batch size = %d is one %dth of the total dataset' % (batch_size,batch_div))
  print('x translation mu = %f var = %f' % (np.mean(arr(transx)),np.var(arr(transx)))) 
  print('y translation mu = %f var = %f' % (np.mean(arr(transy)),np.var(arr(transy))))
  print('###') 
  print('rot angle mu = %f var = %f' % (np.mean(arr(rots)),np.var(arr(rots)))) 
  print('###') 
  print('scaling x mu = %f var = %f' % (np.mean(arr(scalingx)),np.var(arr(scalingx)))) 
  print('scaling y mu = %f var = %f' % (np.mean(arr(scalingy)),np.var(arr(scalingy))))
  print('###')
  print('shear mu = %f var = %f' % (np.mean(arr(shearx)),np.var(arr(shearx))))
  print('###')
  print('reflected %d not-reflected %d' % (refls.count(-1),refls.count(1)))
  print('###')
  print('r2 scores mu = %f var = %f' % (np.mean(arr(r2s)),np.var(arr(r2s))))


"""
attempts a 3D plot of the speed. generally looks bad

freq: the sampling rate, intended for downsampling the points
diff_shift: the finite difference approximation shift value, i.e. you 
            take differences between x[t + shift] and x[t - shift]
xlabel,ylabel: either x_pth or x_trk (or y) depending on which route you 
               are plotting
"""
def show_speed(merged,xlabel,ylabel,title,freq='0.1S',diff_shift=2):
  xs = 'x_pth'
  ys = 'y_pth'

  # downsample
  merged = merged.set_index('t').resample(freq).pad()

  # finite difference appr.x of velocity
  merged['dx'] = merged[xlabel].diff(diff_shift) - merged[xlabel].diff(-1*diff_shift)
  merged['dy'] = merged[ylabel].diff(diff_shift) - merged[ylabel].diff(-1*diff_shift)
  # speed is generally off by a constant for this report, unless dt = 0.5s, but thats fine
  merged['dx'] /= (diff_shift+1)
  merged['dy'] /= (diff_shift+1)
  merged['speed'] = np.sqrt(merged['dx']**2 + merged['dy']**2)

  # remove any nans (shouldn't happen, except in first slot)
  merged = merged.dropna(axis=0,how='any')

  # plot it
  fig = plt.figure()
  ax = fig.add_subplot(projection='3d')
  ax.set_xlabel('x')
  ax.set_ylabel('y')
  ax.set_zlabel('speed')
  ax.set_title(title)
  ax.scatter(merged[xlabel],merged[ylabel],merged['speed'],color='purple')
  plt.show()






