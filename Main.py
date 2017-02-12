import os, sys
import mayavi.mlab as mi
import numpy as np
import scipy.io

import nextBestViewLib as nbv
import matplotlib.pyplot as plt
import mitsubaWrapperLib as mitLib
import miscGeometry as mgo

from time import gmtime, strftime
    
## SET PARAMETERS:
params = {}
params['sampleCount'] = 100 # Samlpes per pixel
params['camWidth']    = 400 # Image width
params['camHeight']   = 400 # Image hight

## Set all file paths:
base_path    = r'C:\Users\addalin\mitsuba_sim\3D_models'.replace('\\', '/')
resultsPath = r'C:\Users\addalin\mitsuba_sim\sim_results'.replace('\\', '/') 

scene_name = 'hetvol'#''cube_with_texture'##hetvol' ##'
shape_filename   = base_path + '/' + scene_name + '/mitsuba/' + scene_name + '.serialized'
boundsPLYPath = base_path + '/' + scene_name + '/' + 'bounds' + '.ply'
screenPLYPath = base_path + '/'  + scene_name + '/' + 'wideScreen' + '.ply'
                     
## PARAMETERS
do_plot = 0

## creating cameras on an arch path
numViews = 6
camsRadius = 3
camsHeight = 0
archAngleSize = 125
upDirection = np.array([0,0,1])
horizon = np.array([0, 1, 0])
boundsTranslation = np.array([0, 0, 0])  # target
screenTranslation = np.array([0, 1, 0])  # screen behind the target

cams = mgo.createCamsCirc(numViews , camsRadius , camsHeight , upDirection , boundsTranslation , archAngleSize , horizon)


## BUILD AND SHOW SCENE
if do_plot:
    scene = nbv.Scene(boundsPLYPath , boundsTranslation , screenPLYPath , screenTranslation)
    scene.addCam(cams)
    #scene.addLight(lights)
    camScale = 0.2
    scene.showSystem(do_plot,camScale)



## RUN MITSUBA
mitsuba = mitLib.Mitsuba(base_path,scene_name,params)
mitsuba.SetSunSky(np.array([[3, 3,300, 0,0,0, 0,0,1]]))

# Rendering the scene
simIm = np.zeros((cams.shape[0],), dtype=np.object)
for i, cam in enumerate (cams):
    mitCam = mgo.rotScene2Mitsuba(cam[None,:])
    mitsuba.SetCamera(mitCam[None,:])    
    #light_curr = np.hstack((np.random.random([1,3])+cams[i][0:3],-cams[i][0:3][None,:]+cams[i][3:6][None,:],up_dir[None,:]))
    #mitsuba.SetSpotlight(light_curr)
    simIm[i] = mitsuba.Render(params['sampleCount'])
    print 'Rendered '+str(i + 1)+'/'+str(numViews)

## PLOT RESULT
if 1:
    for i, im in enumerate(simIm):
        plt.subplot(1,numViews,i+1)
        plt.imshow(im,vmin=0.0,vmax=5.0)
        plt.axis('off')
    plt.show()

print 'Done rendering'

resTime = strftime("%d-%m-%Y_%H-%M-%S", gmtime())
saveRes =  raw_input('Do you want to save resutls [ "y" | "n" ]: ')
if saveRes == 'y':
    
    save_file_name = scene_name + "_" + resTime #raw_input('Enter file name: ')
    sceneParams = {'nViews': numViews, 'camsRadius': camsRadius, 'camsHeight': camsHeight, 'archAngleSize': archAngleSize, 'upDirection': upDirection,
                   'horizon': horizon, 'boundsTranslation': boundsTranslation, 'screenTranslation': screenTranslation,}
    
    scipy.io.savemat(resultsPath + "/" + save_file_name +'_pyCams.mat'  , mdict={'cams': cams , 'camMitsubaParam': params, 'sceneParams': sceneParams})
    scipy.io.savemat(resultsPath + "/" + save_file_name +'_pyImages.mat', {'result_image':simIm})
    
    print resTime, " results are saved at: ", resultsPath
    
    
