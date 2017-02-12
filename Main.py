import os, sys
import mayavi.mlab as mi
import numpy as np
import scipy.io

import nextBestViewLib as nbv
import matplotlib.pyplot as plt
import mitsubaWrapperLib as mitLib
import miscGeometry as mgo  
    
## SET PARAMETERS:
params = {}
params['sampleCount'] = 100 # Samlpes per pixel
params['camWidth']    = 400 # Image width
params['camHeight']   = 400 # Image hight

## Set all file paths:
scene_name = 'hetvol'#''cube_with_texture'##hetvol' ##'
base_path    = r'C:/Users/addalin/mitsuba_sim/3D_models/'
shape_filename   = base_path + scene_name + '/mitsuba/' + scene_name + '.serialized'
boundsPLYPath = base_path + scene_name + '/' + 'bounds' + '.ply'
screenPLYPath = base_path + scene_name + '/' + 'screen' + '.ply'
                     
## PARAMETERS
do_plot = 1

## creating cameras on an arch path
upDirection = np.array([0,0,1])
target = np.array([0 , 0 , 0])
numViews = 6
radius = 3
camsHeight = 0
archAngleSize = 125
#acrchCenter = 270  #TODO: change later to center direction = [0,-1,0]
screenDirection = np.array([0, 1, 0]) 
cams = mgo.createCamsCirc(numViews , radius , camsHeight , upDirection , target , archAngleSize , screenDirection)


## BUILD AND SHOW SCENE
if do_plot: 
    #scene = nbv.Scene(boundsPLYPath)
    scene = nbv.Scene(boundsPLYPath, [0, 0, 0], screenPLYPath, [0, 1, 0])
    scene.addCam(cams)
    #scene.addLight(lights)
    camScale = 0.2
    scene.showSystem(do_plot,camScale)



## RUN MITSUBA
mitsuba = mitLib.Mitsuba(base_path,scene_name,params)
mitsuba.SetSunSky(np.array([[3, 3,300, 0,0,0, 0,0,1]]))

result_image = np.zeros((cams.shape[0],), dtype=np.object)
#result_image = [[] for i in range(cams.shape[0])]
for i in range(cams.shape[0]):
    
    #mitsuba.SetCamera(cams[i][None,:])
    mitCam = mgo.rotScene2Mitsuba(cams[i][None,:])
    mitsuba.SetCamera(mitCam[None,:])    
    #light_curr = np.hstack((np.random.random([1,3])+cams[i][0:3],-cams[i][0:3][None,:]+cams[i][3:6][None,:],up_dir[None,:]))
    #mitsuba.SetSpotlight(light_curr)
    result_image[i] = mitsuba.Render(params['sampleCount'])
    print 'Rendered '+str(i)+'/'+str(cams.shape[0])

## PLOT RESULT
if 1:
    for i in range(len(result_image)):
        plt.subplot(1,cams.shape[0],i+1)
        plt.imshow(result_image[i],vmin=0.0,vmax=5.0)
        plt.axis('off')
    plt.show()

print 'Done rendering'

save_file_name = raw_input('Enter file name: ')

scipy.io.savemat(r'C:\Users\addalin\mitsuba_sim\opticalprobing'.replace('\\', '/') + "/" + save_file_name+'_pyCams.mat'  , mdict={'cams': cams})
scipy.io.savemat(r'C:\Users\addalin\mitsuba_sim\opticalprobing'.replace('\\', '/') + "/" + save_file_name+'_pyImages.mat', {'result_image':result_image})


