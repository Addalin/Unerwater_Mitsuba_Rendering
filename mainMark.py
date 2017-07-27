import os, sys
#import mayavi.mlab as mi
import numpy as np
import scipy.io

import nextBestViewLib as nbv
import matplotlib.pyplot as plt
import markMitsubaLib as mit

# SET PARAMETERS:
params = {}
params['sampleCount'] = 50 # Samlpes per pixel
params['camWidth']    = 500 # Image width
params['camHeight']   = 500 # Image hight

# Set all file paths:
scene_name = 'hetvol' #'cube_with_texture'
base_path    = r'C:\Users\addalin\mitsuba_sim\3D_models'
shape_filename   = base_path + scene_name + '/mitsuba/' + scene_name + '.serialized'
texture_filename = base_path + scene_name + '/mitsuba/textures/' + scene_name + '.png'


# PARAMETERS

#num_images = 60
#theta   = np.linspace(0 , 2*np.pi, num_images+1)
#theta   = theta[0:-1]
#x_cam   = 5 * np.sin(theta)
#y_cam   = 5 * np.cos(theta)

#cams    = np.vstack((x_cam,y_cam)).transpose()
#cams    = np.hstack((cams,
                     #2*np.ones([cams.shape[0],1]),
                     #np.zeros([cams.shape[0],5]),
                     #np.ones([cams.shape[0],1])
                     #))
                     
# PARAMETERS
do_plot = True
space_between_vert = 10
xyz_vec = np.array([[12, -2,0],
                    [8,  -2,0],
                    [8,   2,0],
                    [12,  2,0],
                    [12, -2,0]])

cams = makePolygonPath(space_between_vert,xyz_vec)

#lights  = np.array([[3, 0,0, 0,0,0, 0,0,1],
#                   [1,-6,0, 0,0,0, 0,0,1]]) 


# BUILD AND SHOW SCENE
scene = nbv.Scene(base_path + scene_name + '/' + scene_name + '.ply')
scene.addCam(cams)
#scene.addLight(lights)
#if do_plot:
#    scene.showSystem()


# RUN MITSUBA
mitsuba = mit.Mitsuba(base_path,scene_name,params)
mitsuba.SetSunSky(np.array([[3, 3,300, 0,0,0, 0,0,1]]))

result_image = np.zeros((cams.shape[0],), dtype=np.object)
#result_image = [[] for i in range(cams.shape[0])]
for i in range(cams.shape[0]):
    mitsuba.SetCamera(cams[i][None,:])
    #mitsuba.SetSpotlight(lights[i][None,:])
    result_image[i] = mitsuba.Render(params['sampleCount'])
    print 'Rendered '+str(i)+'/'+str(cams.shape[0])

# PLOT RESULT
if do_plot:
    for i in range(len(result_image)):
        plt.subplot(1,cams.shape[0],i+1)
        plt.imshow(result_image[i],vmin=0.0,vmax=1.0)
        plt.axis('off')
    plt.show()

print 'Done rendering'

#filename = 'square10'
#scipy.io.savemat('C:/Users/markshe/Dropbox/Research/CodeAtmosImaging/opticalprobing_v1.0.0/opticalprobing/DiffusionMaps/'+filename+'_pyCams.mat'  , mdict={'cams': cams})
#scipy.io.savemat('C:/Users/markshe/Dropbox/Research/CodeAtmosImaging/opticalprobing_v1.0.0/opticalprobing/DiffusionMaps/'+filename+'_pyImages.mat', {'result_image':result_image})


# --------- FUNCTIONS --------- 
def makePolygonPath(space_between_vert,xyz_vec):
    t = np.linspace(0 , 1, space_between_vert+1)[:,None]
    t = t[0:-1]
 
    xyz_cam = np.empty((0,3))
    for row in range(xyz_vec.shape[0]-1):
        curr_vec = (1-t)*np.tile(xyz_vec[row][None,:],(space_between_vert,1)) + t *np.tile(xyz_vec[row+1][None,:],(space_between_vert,1))
        #print curr_vec 
        xyz_cam = np.vstack((xyz_cam,curr_vec))
    
    cams    = np.hstack((xyz_cam,xyz_cam + np.array([-1 ,0 ,0]),
                         np.zeros([xyz_cam.shape[0],2]),
                         np.ones([xyz_cam.shape[0],1])
                         )) 
    return cams
