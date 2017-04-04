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
params['sampleCount'] = 10#1024 #128 # Samlpes per pixel
params['samplerDimention'] = 4
params['camWidth']    = 100 #1936 # 2464 # 800  # 400 # Image width
params['camHeight']   = 100 #1458 #  2056 #800   # 400 # Image hight
#params['focalLength'] =  '12'  # focalLength in [mm]
params['fov'] = 39.00829097
params['fovAxis'] = 'x'
params['sensorName'] =  'ICX674' #'IMX264'
params['lenseName'] = ''#'M1214'

## Set all file PATHS:
mitsuba_sim_path = os.environ['MITSUBA_SIM'].replace('\\', '/')
scene_base_path    = mitsuba_sim_path + '/3D_models'  
sub_folder = 'resolution '+ str(params['camWidth']) +' X '+str(params['camHeight'])
resultsPath = mitsuba_sim_path + '/sim_results' + '/' + sub_folder 

#base_path    = '/home/addalin/mitsuba_sim/3D_models/' 
#sub_folder = 'resolution '+ str(params['camWidth']) +' X '+str(params['camHeight'])
#resultsPath = '/home/addalin/mitsuba_sim/sim_results/' + '/' + sub_folder

scene_name = 'hetvol'
shape_filename   = scene_base_path + '/' + scene_name + '/mitsuba/' + scene_name + '.serialized'
boundsPLYPath = scene_base_path + '/' + scene_name + '/' + 'bounds' + '.ply'
screenPLYPath = scene_base_path + '/'  + scene_name + '/' + 'wideScreen' + '.ply'
                     
## Set simulation MODES parameteres
show_scene = 0
show_results = 1
single_view = True
increase_samples = False

## SET screen parameteres
screenTranslation = np.array([0, 2, 0])  # screen behind the target

params['screenWidth'] = 50.0
params['screenHeight'] = 20.0
params['resXScreen'] = 500
params['resYScreen'] = 200 
params['screenZPos'] = 2.0
params['variantRadiance'] = False

## SET common camera's parameteres
camsRadius = 3
camsHeight = 0
upDirection = np.array([0,0,1])
horizon = np.array([0, 1, 0])
boundsTranslation = np.array([0, 0, 0])  # target

## RUN MITSUBA & ADD lights and screen
mitsuba = mitLib.Mitsuba(scene_base_path,scene_name,params)
#mitsuba.SetSunSky(np.array([[3, 300,3, 0,0,0, 0,0,1]]))
#mitsuba.SetWideScreen(screenWidth , screenHeight,resXScreen,resYScreen, screenZPos,True)


## RUN scenarios (varaing views positions)
nImgsNoise = 1
numImsOp = np.array([nImgsNoise])  # np.array([4, 5, 6, 7, 8])
for numIms in numImsOp:
    
    ## SET cameras' positions for current scenario 
    # Arch cameras positioning 
    if single_view :
        archAngleSize = 0
        cams = mgo.createCamsCirc(1 , camsRadius , camsHeight , upDirection , boundsTranslation , archAngleSize , horizon)  
        mitCam = mgo.rotScene2Mitsuba(cams[0][None,:])         
    else:
        archAngleSize = 125
        cams = mgo.createCamsCirc(numIms , camsRadius , camsHeight , upDirection , boundsTranslation , archAngleSize , horizon)
    
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
        scene.showSystem(do_plot,camScale)
    
    
    ## RENDER the scene
    simIm = np.zeros(numIms,dtype=np.object) #((cams.shape[0],), dtype=np.object)
    currSceneInfo = []
    #for i, cam in enumerate (cams):
    for i in range (0,numIms):
        if not(single_view):
            mitCam = mgo.rotScene2Mitsuba(cams[i][None,:])
            
        mitsuba.SetCamera(mitCam[None,:])
        if increase_samples:
            # increasing samples count - this is for noise statistics: variance vs. samplesCount; increasing every 10 images 
            params['sampleCount'] = params['sampleCount']*2 if (np.mod(numIms,10)==0 & numIms>1) else params['sampleCount']
        simIm[i] , sceneInfo = mitsuba.Render(params['sampleCount'],i)
        currSceneInfo.append(sceneInfo)
        print 'Rendered '+str(i + 1)+'/'+str(numIms)
    
    ## PLOT RESULT
    if show_results:
        for i, im in enumerate(simIm):
            plt.subplot(1,numIms,i+1)
            plt.imshow(im,vmin=0.0,vmax= 1.0)
            plt.axis('off')
        plt.show()
    
    print 'Done rendering'
    
    ## SAVE results:
    resTime = strftime("%d-%m-%Y_%H-%M-%S", gmtime())
    #saveRes = raw_input('Do you want to save resutls [ "y" | "n" ]: ')
    #if saveRes == 'y':
    #if numIms == nImgsNoise :
    if single_view :

        scene_type = 'cloud_single_view' + str(numIms) + 'images'+'_cloud_for_stats'
    else:
        scene_type = 'cloud_' + str(numIms) + 'views' 
        
    save_file_name = scene_name + "_" + resTime + "_" + scene_type     
    save_file_name = scene_name + "_" + resTime + "_" + scene_type #raw_input('Enter file name: ')
    sceneParams = {'nViews': numIms, 'camsRadius': camsRadius, 'camsHeight': camsHeight, 'archAngleSize': archAngleSize, 'upDirection': upDirection,
                   'horizon': horizon, 'boundsTranslation': boundsTranslation, 'screenTranslation': screenTranslation,}
    
    scipy.io.savemat(resultsPath + "/" + save_file_name +'_pyCams.mat'  , mdict={'camsLookAtVectors': cams , 'camsMitsubaParam': params, 'sceneMitsubaParams': sceneParams})
    scipy.io.savemat(resultsPath + "/" + save_file_name +'_pyImages.mat', {'renderedImagesMitsuba':simIm})
    #scipy.io.savemat(resultsPath + "/" + save_file_name +'_pySceneInfo.mat', mdict = {'scene_info':sceneInfo})
    
    print resTime, 'scene type:'+scene_type+' has finished. \nResults are saved at: ', resultsPath
    
    
