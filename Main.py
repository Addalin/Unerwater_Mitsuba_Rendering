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
params['camWidth']    = 100  #2464 # 800  # 400 # Image width
params['camHeight']   =   100  #2056 #800   # 400 # Image hight
#params['focalLength'] =  '12'  # focalLength in [mm]
params['fov'] = 39.00829097
params['fovAxis'] = 'x'
params['sensorName'] =  'ICX674' #'IMX264'
params['lenseName'] = ''#'M1214'

## Set all file paths:
mitsuba_sim_path = os.environ['MITSUBA_SIM'].replace('\\', '/')
scene_base_path    = mitsuba_sim_path + '/3D_models'  
sub_folder = 'resolution '+ str(params['camWidth']) +' X '+str(params['camHeight'])
resultsPath = mitsuba_sim_path + '/sim_results' + '/' + sub_folder  

scene_name = 'hetvol' #'cube_with_texture'
shape_filename   = scene_base_path + '/' + scene_name + '/mitsuba/' + scene_name + '.serialized'
boundsPLYPath = scene_base_path + '/' + scene_name + '/' + 'bounds' + '.ply'
screenPLYPath = scene_base_path + '/'  + scene_name + '/' + 'wideScreen' + '.ply'
                     
## Set simulation parameteres
show_scene = 1
show_results = 1

## SET screen parameteres
screenTranslation = np.array([0, 2, 0])  # screen behind the target
screenWidth = 50.0
screenHeight = 20.0
resXScreen = 50
resYScreen = 20
screenDist = 2.0

## SET common camera's parameteres
camsRadius = 3
camsHeight = 0
upDirection = np.array([0,0,1])
horizon = np.array([0, 1, 0])
boundsTranslation = np.array([0, 0, 0])  # target

## RUN MITSUBA & ADD lights and screen
mitsuba = mitLib.Mitsuba(scene_base_path,scene_name,params)
mitsuba.SetSunSky(np.array([[3, 3,300, 0,0,0, 0,0,1]]))
mitsuba.SetWideScreen(screenWidth , screenHeight,resXScreen,resYScreen, screenDist, True)

## RUN scenarios (varaing views positions) 
viewsOp = np.array([1])  # np.array([4, 5, 6, 7, 8])
for numViews in viewsOp:
    
    ## SET cameras' positions for current scenario 
    # Arch cameras positioning     
    if numViews != 10 :
        archAngleSize = 125
    else:
        archAngleSize = 0
    cams = mgo.createCamsCirc(numViews , camsRadius , camsHeight , upDirection , boundsTranslation , archAngleSize , horizon)
    
    # Specipied cameras positioning 
    #xCam   = np.array([-0.5 , -0.25 , 0 ,  0.25 , 0.5])  # np.array([-0.5, -0.25, -0.25, 0.5])
    #yCam   = np.array([ -0.55 , -0.55 , -0.55 , -0.55, -0.55])  # ([]0, -0.25, -0.25 , 0])
    #zCam   = np.array([0, 0, 0 , 0 , 0])
    
    # Retreives numViews of toWorld transform vectors for each camera [self position, target = (0,0,0), up direction = (0,0,1)]
    #camsPos = np.vstack( ( xCam , yCam , zCam ) ).transpose()
    #cams =  mgo.setCamToWorldVec(camsPos , upDirection, boundsTranslation)
    
    ## BUILD AND SHOW SCENE
    if show_scene:
        scene = nbv.Scene(boundsPLYPath , boundsTranslation , screenPLYPath , screenTranslation)
        scene.addCam(cams)
        #scene.addLight(lights)
        camScale = 0.2
        scene.showSystem(show_scene,camScale)
    
    ## RENDER the scene
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
    if show_results:
        for i, im in enumerate(simIm):
            plt.subplot(1,numViews,i+1)
            plt.imshow(im,vmin=0.0,vmax= 1.0)
            plt.axis('off')
        plt.show()
    
    print 'Done rendering'
    
    ## SAVE results:
    resTime = strftime("%d-%m-%Y_%H-%M-%S", gmtime())
    #saveRes = raw_input('Do you want to save resutls [ "y" | "n" ]: ')
    #if saveRes == 'y':
    if numViews != 10 :
        scene_type = 'cloud_' + str(numViews) + 'views_mfilm'
    else:
        scene_type = 'cloud_single_view' + str(numViews) + 'images'
    save_file_name = scene_name + "_" + resTime + "_" + scene_type     
    save_file_name = scene_name + "_" + resTime + "_" + scene_type #raw_input('Enter file name: ')
    sceneParams = {'nViews': numViews, 'camsRadius': camsRadius, 'camsHeight': camsHeight, 'archAngleSize': archAngleSize, 'upDirection': upDirection,
                   'horizon': horizon, 'boundsTranslation': boundsTranslation, 'screenTranslation': screenTranslation,}
    
    scipy.io.savemat(resultsPath + "/" + save_file_name +'_pyCams.mat'  , mdict={'camsLookAtVectors': cams , 'camsMitsubaParam': params, 'sceneMitsubaParams': sceneParams})
    scipy.io.savemat(resultsPath + "/" + save_file_name +'_pyImages.mat', {'renderedImagesMitsuba':simIm})
    #scipy.io.savemat(resultsPath + "/" + save_file_name +'_pySceneInfo.mat', mdict = {'scene_info':sceneInfo})
    
    print resTime, 'scene type:'+scene_type+' has finished. \nResults are saved at: ', resultsPath
    
    
