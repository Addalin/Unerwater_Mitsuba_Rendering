import os, sys
import mayavi.mlab as mi
import numpy as np
import scipy.io

import nextBestViewLib as nbv
import matplotlib.pyplot as plt
import markMitsubaLib as mit
from markCoreLib import rotScene2Mitsuba,rotX
# --------- FUNCTIONS --------- 
def makePolygonPath(space_between_vert,xyz_vec,looking_dir,up_dir):
    t = np.linspace(0 , 1, space_between_vert+1)[:,None]
    t = t[0:-1]
 
    xyz_cam = np.empty((0,3))
    for row in range(xyz_vec.shape[0]-1):
        curr_vec = (1-t)*np.tile(xyz_vec[row][None,:],(space_between_vert,1)) + t *np.tile(xyz_vec[row+1][None,:],(space_between_vert,1))
        #print curr_vec 
        xyz_cam = np.vstack((xyz_cam,curr_vec))
    
    cams    = np.hstack((xyz_cam,xyz_cam +looking_dir,np.zeros(xyz_cam.shape) + up_dir)) 
    return cams


def makeCircPath(num_images,radius,z):
    
    theta   = np.linspace(0 , 2*np.pi, num_images+1)
    theta   = theta[0:-1]
    x_cam   = radius * np.sin(theta)
    y_cam   = radius * np.cos(theta)
    
    cams    = np.vstack((x_cam,y_cam)).transpose()
    cams    = np.hstack((cams,
        z*np.ones([cams.shape[0],1]),
        np.zeros([cams.shape[0],5]),
        np.ones([cams.shape[0],1])
        ))   
    
    return cams
    
# SET PARAMETERS:
params = {}
params['sampleCount'] = 100 # Samlpes per pixel
params['camWidth']    = 400 # Image width
params['camHeight']   = 400 # Image hight

# Set all file paths:
scene_name = 'hetvol'#''cube_with_texture'##hetvol' ##'
bound_name = 'bounds'
base_path    = r'C:/Users/addalin/mitsuba_sim/3D_models/'
shape_filename   = base_path + scene_name + '/mitsuba/' + scene_name + '.serialized'
#texture_filename = base_path + scene_name + '/mitsuba/textures/' + scene_name + '.png'
                     
# PARAMETERS
do_plot = 1

space_between_vert = 2
xyz_vec = np.array([[0,0,3],
                    [0,2,3],
                    [2,2,3],
                    [2,0,3],
                    [0,0,3]])
looking_dir = np.array([0,0,-1])
up_dir      = np.array([1,0,0])
#cams = makePolygonPath(space_between_vert,xyz_vec,looking_dir,up_dir)

num_images = 8
radius = 2
z = 0.5
cams = makeCircPath(num_images,radius,z)

# BUILD AND SHOW SCENE
if do_plot:    
    scene = nbv.Scene(base_path + scene_name + '/' + bound_name + '.ply')
    scene.addCam(cams)
    #scene.addLight(lights)
    scene.showSystem(1,1)



# RUN MITSUBA
mitsuba = mit.Mitsuba(base_path,scene_name,params)
mitsuba.SetSunSky(np.array([[3, 3,300, 0,0,0, 0,0,1]]))

result_image = np.zeros((cams.shape[0],), dtype=np.object)
#result_image = [[] for i in range(cams.shape[0])]
for i in range(cams.shape[0]):
    
    #mitsuba.SetCamera(cams[i][None,:])
    mitCam = rotScene2Mitsuba(cams[i][None,:])
    mitsuba.SetCamera(mitCam[None,:])    
    light_curr = np.hstack((np.random.random([1,3])+cams[i][0:3],-cams[i][0:3][None,:]+cams[i][3:6][None,:],up_dir[None,:]))
    mitsuba.SetSpotlight(light_curr)
    result_image[i] = mitsuba.Render(params['sampleCount'])
    print 'Rendered '+str(i)+'/'+str(cams.shape[0])

# PLOT RESULT
if 1:
    for i in range(len(result_image)):
        plt.subplot(1,cams.shape[0],i+1)
        plt.imshow(result_image[i],vmin=0.0,vmax=1.0)
        plt.axis('off')
    plt.show()

print 'Done rendering'

#save_file_name = raw_input('Enter file name: ')

#scipy.io.savemat('C:/Users/markshe/Dropbox/Research/CodeAtmosImaging/opticalprobing_v1.0.0/opticalprobing/DiffusionMaps/'+save_file_name+'_pyCams.mat'  , mdict={'cams': cams})
#scipy.io.savemat('C:/Users/markshe/Dropbox/Research/CodeAtmosImaging/opticalprobing_v1.0.0/opticalprobing/DiffusionMaps/'+save_file_name+'_pyImages.mat', {'result_image':result_image})


