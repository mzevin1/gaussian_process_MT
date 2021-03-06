# import packages
import numpy as np
import scipy as sp
import pandas as pd
import time
import os
import pdb
import argparse
import itertools
import pickle

import matplotlib
matplotlib.use("agg")
import matplotlib.pyplot as plt
import matplotlib.pylab as pylab
from matplotlib import gridspec
from matplotlib.collections import LineCollection
from mpl_toolkits.mplot3d import Axes3D


# read in arguments
argp = argparse.ArgumentParser()
argp.add_argument("-pd", "--pickle-directory", type=str, default='.', help="Name of the pickle directory. Default='.'.")
argp.add_argument("-f", "--run-tag", help="Use this as the stem for all file output.")
argp.add_argument("-d", "--out-dir", type=str, default=None, help="The output directory (underneath 'plots/') for the figures. Default will be the same as the pickle directory.")
args = argp.parse_args()

# set output directory under 'plots/' to the pickle directory if not specified
if not args.out_dir:
    args.out_dir = args.pickle_directory

# path to the directory that has all the resampled files you wish to use
basepath = os.getcwd()
pickle_path = basepath + '/pickles/' + args.pickle_directory + '/'


# make subdirectory in "plots" for the plots
if args.out_dir:
    if not os.path.exists("plots/" + args.out_dir):
        os.makedirs("plots/" + args.out_dir)
    pltdir = 'plots/'+args.out_dir+'/'
else:
    if not os.path.exists("plots/"):
        os.makedirs("plots/")
    pltdir = 'plots/'


# read in the pickles
params=[]
pickles={}
for p in os.listdir(pickle_path):
    params.append(p[:-7])
    pickles[p[:-7]] = pickle.load(open(pickle_path+p, "rb"))
inputs = pickles[params[0]]['inputs'] # these will be the same for all output parameters since we specify random seed
full_inputs = pickles[params[0]]['full_inputs']
X_test = pickles[params[0]]['X_test']
X_train = pickles[params[0]]['X_train']
steps = pickles[params[0]]['y_train'].shape[1]


# pick random testing point for plotting purposes (for testMT, it is the only available track)
t = np.random.randint(0,len(X_test)) # choose random testing track to plot, or specify number
print 'Testing point properties:'
print '   Mbh_init : %f' % X_test.iloc[t]['Mbh_init']
print '   M2_init : %f' % X_test.iloc[t]['M2_init']
print '   P_init : %f' % 10**X_test.iloc[t]['P_init']
print '   Z_init : %f' % 10**X_test.iloc[t]['Z_init']


### Plot initial condition of entire dataset, and training vs testing set ###
fig=plt.figure(figsize = (15,12), facecolor = 'white')
ax = fig.add_subplot(111, projection='3d')
ax.set_zlabel('$Black\ Hole\ Mass\ (M_{\odot})$', rotation=0, labelpad=20, size=12)
ax.set_ylabel('$Companion\ Mass\ (M_{\odot})$', rotation=0, labelpad=20, size=12)
ax.set_xlabel('$Log\ Period\ (s)$', rotation=0, labelpad=20, size=12)

pts = ax.scatter(np.array(X_train['P_init']), np.array(X_train['M2_init']), np.array(X_train['Mbh_init']), zdir='z', cmap='viridis', c=np.array(X_train['Z_init']), vmin=inputs["Z_init"].min(), vmax=inputs["Z_init"].max(), marker='.', s=10, label='training tracks')
ax.scatter(np.array(X_test['P_init']), np.array(X_test['M2_init']), np.array(X_test['Mbh_init']), zdir='z', cmap='viridis', c=np.array(X_test['Z_init']), vmin=inputs["Z_init"].min(), vmax=inputs["Z_init"].max(), marker='*', s=20, label='testing tracks')
ax.scatter(X_test['P_init'].iloc[t], X_test['M2_init'].iloc[t], X_test['Mbh_init'].iloc[t], zdir='z', cmap='viridis', c=X_test['Z_init'].iloc[t], vmin=inputs["Z_init"].min(), vmax=inputs["Z_init"].max(), marker='*', s=200, label='plotted point')
fig.colorbar(pts)
plt.legend()

plt.tight_layout()
if args.run_tag:
    fname = pltdir + args.run_tag + '_param_space.png'
else:
    fname = pltdir + 'param_space.png'
plt.savefig(fname)



### Plot evolution comparison for a given track ###
f, axs = plt.subplots(nrows = len(params), sharex=True, figsize=(8,2*len(params)))
for idx, p in enumerate(params):
    # setup axes
    if idx==len(params)-1:
        axs[idx].set_xlabel('Resampled Step')
    axs[idx].set_ylabel(p)
    #if idx==0:
        #axs[idx].set_title('Interpolation for Testing Track M2: '+str(X_test['M2_init'].iloc[t])+', Mbh: '+str(X_test['Mbh_init'].iloc[t])+', P: '+str(X_test['P_init'].iloc[t])+', Z: '+str(X_test['Z_init'].iloc[t]))
    axs[idx].set_xlim(0-steps/100., steps+steps/100.)   # add some buffer to the plot

    # do plotting
    param = pickles[p]
    axs[idx].plot(np.linspace(0,steps,steps), param['y_test'][t,:], 'k', linewidth=1, alpha=0.5, label='actual evolution')
    axs[idx].plot(np.linspace(0,steps,steps), param['linear'][t,:], 'g', linewidth=0.5, alpha=0.5, label='linear interpolated evolution')
    axs[idx].plot(np.linspace(0,steps,steps), param['GP'][t,:], 'b', linewidth=0.5, alpha=0.5, label='GP interpolated evolution')
    axs[idx].fill_between(np.linspace(0,steps,steps), param['GP'][t,:]-param['error'][t,:], param['GP'][t,:]+param['error'][t,:], alpha=0.05, label='GP error')
plt.legend()
if args.run_tag:
    fname = pltdir + args.run_tag + '_test_evolution.png'
else:
    fname = pltdir + 'test_evolution.png'
plt.tight_layout()
plt.savefig(fname)


### Plot the average error for each output parameter, scaled by the range of the output in question ###

def mean_exp_error(exp,act):
    exp_err = np.abs((exp-act)/act)
    return exp_err.mean()*100, exp_err.std()*100

f, axs = plt.subplots(nrows=1, ncols=1, figsize=(12,4))
# setup axes
axs.set_xlabel('Parameter')
axs.set_ylabel('Percent Error (%)')
axs.set_title('Average Percent Error for Interpolation Methods')
axs.set_xlim(-1, len(params)) # add some buffer to the plot
axs.set_ylim(0,10)
plt.xticks(range(len(params)), params)


# do plotting
for idx, p in enumerate(params):
    print idx, p
    param = pickles[p]
    # FIXME it would be good to return these values below for comparison...
    GP_err, GP_std = mean_exp_error(param['GP'],param['y_test'])
    lin_err, lin_std = mean_exp_error(param['linear'],param['y_test'])
    axs.scatter(idx-0.2, GP_err, c='b', marker='*')
    axs.scatter(idx+0.2, lin_err, c='g', marker='*')
    axs.errorbar(idx-0.2, GP_err, c='b', yerr=GP_std, label='average GP error')
    axs.errorbar(idx+0.2, lin_err, c='g', yerr=lin_std, label='average linear error')
    if idx==0:
        plt.legend(loc='upper right')

if args.run_tag:
    fname = pltdir + args.run_tag + '_global_err.png'
else:
    fname = pltdir + 'global_err.png'
plt.tight_layout()
plt.savefig(fname)


### See how GP-predicted error corellates to actual error ###
# FIXME this isn't working...

def abs_err(exp,act):
    err = np.abs(exp-act)
    return err

f, axs = plt.subplots(nrows=len(params), ncols=1, figsize=(9,3*len(params)))

# do plotting
for idx, p in enumerate(params):
    # setup axes
    axs[idx].set_title(p)
    axs[idx].set_ylabel('Actual error')
    if idx == len(params)-1:
        axs[idx].set_xlabel('GP error')
    param = pickles[p]
    actual_error = abs_err(param['GP'],param['y_test'])
    axs[idx].scatter(param['error'].flatten(), actual_error.flatten(), c='k', marker='.')

if args.run_tag:
    fname = pltdir + args.run_tag + '_error_comp.png'
else:
    fname = pltdir + 'error_comp.png'
plt.tight_layout()
plt.savefig(fname)


### Plot 2d evolution with GP errors ###
f, axs = plt.subplots(nrows = 2, sharex=True, figsize=(8,6))

# setup axes
axs[0].set_ylabel(r'$\dot{M}_2$')
axs[1].set_xlabel(r'$age$')
axs[1].set_ylabel(r'$log(T_{eff})$')

# choose the 2d parameters to plot
x0='age'
y0='lg_mstar_dot_1'
x1='age'
y1='log_Teff'

# do plotting
axs[0].plot(pickles[x0]['y_test'][t,:], pickles[y0]['y_test'][t,:], 'k', linewidth=1, alpha=0.5, label='actual evolution')
axs[0].plot(pickles[x0]['linear'][t,:], pickles[y0]['linear'][t,:], 'g', linewidth=0.5, alpha=0.5, label='linear interpolated evolution')
#axs[0].plot(pickles[x0]['GP'][t,:], pickles[y0]['GP'][t,:], 'b', linewidth=0.5, alpha=0.5, label='GP interpolated evolution')
#axs[0].errorbar(pickles[x0]['GP'][t,:], pickles[y0]['GP'][t,:], yerr=pickles[y0]['error'][t,:], color='b', alpha=0.01)
for i in xrange(len(pickles[x0]['y_train'])):
    if i==0:
        axs[0].plot(pickles[x0]['y_train'][i,:], pickles[y0]['y_train'][i,:], 'k', linewidth=1, alpha=0.05, label='testing tracks')
    else:
        axs[0].plot(pickles[x0]['y_train'][i,:], pickles[y0]['y_train'][i,:], 'k', linewidth=1, alpha=0.05)
pts = axs[0].scatter(pickles[x0]['GP'][t,:], pickles[y0]['GP'][t,:], cmap='viridis', c=pickles[y0]['error'][t,:], vmin=pickles[y0]['error'][t,:].min(), vmax=pickles[y0]['error'][t,:].max(), marker='.', s=5, label='GP interpolated evolution')

axs[1].plot(pickles[x1]['y_test'][t,:], pickles[y1]['y_test'][t,:], 'k', linewidth=1, alpha=0.5, label='actual evolution')
axs[1].plot(pickles[x1]['linear'][t,:], pickles[y1]['linear'][t,:], 'g', linewidth=0.5, alpha=0.5, label='linear interpolated evolution')
#axs[1].plot(pickles[x1]['GP'][t,:], pickles[y1]['GP'][t,:], 'b', linewidth=0.5, alpha=0.5, label='GP interpolated evolution')
#axs[1].errorbar(pickles[x1]['GP'][t,:], pickles[y1]['GP'][t,:], yerr=pickles[y1]['error'][t,:], color='b', alpha=0.01)
for i in xrange(len(pickles[x1]['y_train'])):
    if i==0:
        axs[1].plot(pickles[x1]['y_train'][i,:], pickles[y1]['y_train'][i,:], 'k', linewidth=1, alpha=0.05, label='testing tracks')
    else:
        axs[1].plot(pickles[x1]['y_train'][i,:], pickles[y1]['y_train'][i,:], 'k', linewidth=1, alpha=0.05)
pts = axs[1].scatter(pickles[x1]['GP'][t,:], pickles[y1]['GP'][t,:], cmap='viridis', c=pickles[y1]['error'][t,:], vmin=pickles[y1]['error'][t,:].min(), vmax=pickles[y1]['error'][t,:].max(), marker='.', s=5, label='GP interpolation & error')
axs[1].set_xlim(1e7,2e7)
plt.legend(loc='upper left', prop={'size': 6})

# add colorbar
f.subplots_adjust(right=0.82)
cbar_ax = f.add_axes([0.85, 0.15, 0.05, 0.7])
cbar = f.colorbar(pts, ticks=[pickles[y1]['error'][t,:].min(), pickles[y1]['error'][t,:].max()], cax=cbar_ax, orientation='vertical')
cbar.ax.set_yticklabels(['Low', 'High'])


if args.run_tag:
    fname = pltdir + args.run_tag + '_2d_test_evolution.png'
else:
    fname = pltdir + '2d_test_evolution.png'
plt.savefig(fname)
