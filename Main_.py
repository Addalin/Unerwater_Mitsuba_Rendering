import os, sys
import mayavi.mlab as mi
import numpy as np
import scipy.io

import nextBestViewLib as nbv
import matplotlib.pyplot as plt
import mitsubaWrapperLib as mitLib
import miscGeometry as mgo
import timeit
from time import gmtime, strftime
start = timeit.default_timer()

    
## SET PARAMETERS:
params = {}
params['sampleCount'] = 100 # Samlpes per pixel
params['camWidth']    =  800#2464  # 400 # Image width
params['camHeight']   =  800#2056   # 400 # Image hight
params['focalLength'] =  '12'  # focalLength in [mm]
params['fov'] = 40.4
params['fovAxis'] = 'x'
params['sensorName'] = 'IMX264'
params['lenseName'] = 'M1214'

## Set all file paths:
base_path    = r'.\3D_models'.replace('\\', '/')
resultsPath = r'.\sim_results'.replace('\\', '/') 

scene_name = 'hetvol'#''cube_with_texture'##hetvol' ##'
shape_filename   = base_path + '/' + scene_name + '/mitsuba/' + scene_name + '.serialized'
boundsPLYPath = base_path + '/' + scene_name + '/' + 'bounds' + '.ply'
screenPLYPath = base_path + '/'  + scene_name + '/' + 'wideScreen' + '.ply'
                     
## PARAMETERS
do_plot = 0


## creating cameras on an arch path
numViews = 1
camsRadius = 3
camsHeight = 0
archAngleSize = 125
upDirection = np.array([0,0,1])
horizon = np.array([0, 1, 0])
boundsTranslation = np.array([0, 0, 0])  # target
screenTranslation = np.array([0, 2, 0])  # screen behind the target

# Arch camera positioning out side of the volume
cams = mgo.createCamsCirc(numViews , camsRadius , camsHeight , upDirection , boundsTranslation , archAngleSize , horizon)
# Cameras positioning within the volume
#xCam   = np.array([-0.5 , -0.25 , 0 ,  0.25 , 0.5])  # np.array([-0.5, -0.25, -0.25, 0.5])
#yCam   = np.array([ -0.55 , -0.55 , -0.55 , -0.55, -0.55])  # ([]0, -0.25, -0.25 , 0])
#zCam   = np.array([0, 0, 0 , 0 , 0])

# Retreives numViews of toWorld transform vectors for each camera [self position, target = (0,0,0), up direction = (0,0,1)]
#camsPos = np.vstack( ( xCam , yCam , zCam ) ).transpose()
#cams =  mgo.setCamToWorldVec(camsPos , upDirection, boundsTranslation)

### BUILD AND SHOW SCENE
if do_plot:
    scene = nbv.Scene(boundsPLYPath , boundsTranslation , screenPLYPath , screenTranslation)
    scene.addCam(cams)
    #scene.addLight(lights)
    camScale = 0.2
    scene.showSystem(do_plot,camScale)



## RUN MITSUBA
mitsuba = mitLib.Mitsuba(base_path,scene_name,params)
mitsuba.SetSunSky(np.array([[3, 3,300, 0,0,0, 0,0,1]]))
start = timeit.default_timer()

# Rendering the scene
simIm = np.zeros((cams.shape[0],), dtype=np.object)
currSceneInfo = []
for i, cam in enumerate (cams):
    mitCam = mgo.rotScene2Mitsuba(cam[None,:])
    mitsuba.SetCamera(mitCam[None,:])    
    #light_curr = np.hstack((np.random.random([1,3])+cams[i][0:3],-cams[i][0:3][None,:]+cams[i][3:6][None,:],up_dir[None,:]))
    #mitsuba.SetSpotlight(light_curr)
    simIm[i] , sceneInfo = mitsuba.Render(params['sampleCount'])
    currSceneInfo.append(sceneInfo)
    print 'Rendered '+str(i + 1)+'/'+str(numViews)

## PLOT RESULT
if 1:
    for i, im in enumerate(simIm):
        plt.subplot(1,numViews,i+1)
        plt.imshow(im,vmin=0.0,vmax=5.0)
        plt.axis('off')
    plt.show()

print 'Done rendering'
stop = timeit.default_start = timeit.default_timer()
runTime = stop - start 
print 'Simulation run time :',runTime ,'[sec]'

resTime = strftime("%d-%m-%Y_%H-%M-%S", gmtime())
saveRes = raw_input('Do you want to save resutls [ "y" | "n" ]: ')
if saveRes == 'y':
    scene_type = 'clouds_4views'
    save_file_name = scene_name + "_" + resTime + "_" + scene_type #raw_input('Enter file name: ')
    sceneParams = {'nViews': numViews, 'camsRadius': camsRadius, 'camsHeight': camsHeight, 'archAngleSize': archAngleSize, 'upDirection': upDirection,
                   'horizon': horizon, 'boundsTranslation': boundsTranslation, 'screenTranslation': screenTranslation,}
    
    scipy.io.savemat(resultsPath + "/" + save_file_name +'_pyCams.mat'  , mdict={'camsLookAtVectors': cams , 'camsMitsubaParam': params, 'sceneMitsubaParams': sceneParams})
    scipy.io.savemat(resultsPath + "/" + save_file_name +'_pyImages.mat', {'renderedImagesMitsuba':simIm})
    #scipy.io.savemat(resultsPath + "/" + save_file_name +'_pySceneInfo.mat', mdict = {'scene_info':sceneInfo})
    
    print resTime, " results are saved at: ", resultsPath
    
    
