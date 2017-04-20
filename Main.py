import os, sys
import mayavi.mlab as mi
import numpy as np
import scipy.io

import nextBestViewLib as nbv
import matplotlib.pyplot as plt
import mitsubaWrapperLib as mitLib
import miscGeometry as mgo

from time import gmtime, strftime
import timeit

## SET PARAMETERS:

params = {}
params['sampleCount'] = 1024 #128 # Samlpes per pixel
params['samplerDimention'] = 4
params['nWidth']    = 100#1936#400#1936 # 2464 # 800  # 400 # Image width
params['nHeight']   = 100#1458#400# 1458 # 2056 # 800  # 400 # Image hight
#params['focalLength'] =  '12'  # focalLength in [mm]
params['fov'] = 39.00829097
params['fovAxis'] = 'x'
params['sensorName'] =  'ICX674' #'IMX264' #
#params['lenseName'] = ''#'M1214'
params['wellDepth'] = 15770.0 # 10361.0 # 

#other parameteres just for results savings
params['readNoise'] = 10.0
params['bitDepth'] = 12
params['du'] = 4.54*(10**-6)
params['dv'] = 4.54*(10**-6)
params['width'] = params['nWidth']*params['du']
params['height'] = params['nHeight']*params['dv']

## Set simulation MODES parameteres
show_scene = False
show_results = True
single_view = True
increase_samples = False
save_results = True             
theme = ['background','cloud']
themeType = 1

## SET screen parameteres
screenTranslation = np.array([0, 2, 0])  # screen behind the target - this translation is for visualization coordinates (not for Mitsuba!!!)
screenParams = {}
screenParams['variantRadiance'] = True
screenParams['screenWidth'] = 50.0
screenParams['screenHeight'] = 20.0
screenParams['resXScreen'] = 500
screenParams['resYScreen'] = 200 
screenParams['screenZPos'] = 2.0
screenParams['maxRadiance'] = 1.5



## SET common camera's parameteres
camsRadius = 3
camsHeight = 0
upDirection = np.array([0,0,1])
horizon = np.array([0, 1, 0])
boundsTranslation = np.array([0, 0, 0])  # target

## SET runing scenarios 
nRuns = 1 #64 #np.ceil(params['wellDepth']/params['sampleCount']).astype(int) # nRuns -  number of runing times for scenario
if single_view:
    nRunOp = np.array([nRuns])
    scenario_path = theme[themeType] + '_single view_' + str(nRuns) +' runs'
else:
    numViews = 4 # numViews - varaing cameras positions   
    nRunOp = np.ones(nRuns,dtype=int)*numViews
    scenario_path = theme[themeType] + '_multiple ' + str(numViews) + ' views_'+str(nRuns) + ' runs'        
    # nRunOp - array size of nRuns, each cell value is numViews; This is for running the scene witn numViews camers X nRuns times     


## Set folders PATHS:
scene_name = 'hetvol'
startTime = strftime("%d-%m-%Y_%H-%M-%S", gmtime())
mitsuba_sim_path = os.environ['MITSUBA_SIM'].replace('\\', '/')
scene_base_path    = mitsuba_sim_path + '/3D_models'                                  #scene_base_path    = '/home/addalin/mitsuba_sim/3D_models/'
if save_results:
    resolution_folder = 'resolution '+ str(params['nWidth']) +' X '+str(params['nHeight'])   #resolution_folder = 'resolution '+ str(params['camWidth']) +' X '+str(params['camHeight'])
    resultsPath = mitsuba_sim_path + '/sim_results' + '/' + resolution_folder + '/' + scenario_path + '_' + startTime                 #resultsPath = '/home/addalin/mitsuba_sim/sim_results/' + '/' + sub_folder
if show_scene:
    shape_filename   = scene_base_path + '/' + scene_name + '/mitsuba/' + scene_name + '.serialized'
    boundsPLYPath = scene_base_path + '/' + scene_name + '/' + 'bounds' + '.ply'
    screenPLYPath = scene_base_path + '/'  + scene_name + '/' + 'wideScreen' + '.ply'

## RUN MITSUBA & ADD lights and screen
mitsuba = mitLib.Mitsuba(scene_base_path,scene_name,params,screenParams)

for runNo,numIms in enumerate(nRunOp):

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
    simIm =  np.zeros(numIms,dtype=np.object) #((cams.shape[0],), dtype=np.object)
    currSceneInfo = []
    tic=timeit.default_timer()     
    for i in range (0,numIms):    #for i, cam in enumerate (cams):
        if not(single_view):
            mitCam = mgo.rotScene2Mitsuba(cams[i][None,:])

        mitsuba.SetCamera(mitCam[None,:])
        if increase_samples:
            # increasing samples count - this is for noise statistics: variance vs. samplesCount; increasing every 10 images 
            params['sampleCount'] = params['sampleCount']*2 if (np.mod(numIms,10)==0 & numIms>1) else params['sampleCount']
        simIm[i] , sceneInfo = mitsuba.Render(params['sampleCount'],i)
        currSceneInfo.append(sceneInfo)
        print 'Rendered '+str(i + 1)+'/'+str(numIms)
    toc = timeit.default_timer()
    renderTime = toc - tic #elapsed time in seconds    

    ## PLOT RESULT
    if show_results:
        for i, im in enumerate(simIm):
            plt.subplot(1,numIms,i+1)
            plt.imshow(im,vmin=0.0,vmax= 1.0)
            plt.axis('off')
        plt.show()

    print 'Done rendering'

    ## SAVE results:
    #resTime = strftime("%d-%m-%Y_%H-%M-%S", gmtime())
    resTime = 'run no '+str(runNo+1)

    if save_results:
        #saveRes = raw_input('Do you want to save resutls [ "y" | "n" ]: ')
        #if saveRes == 'y':
        #if numIms == nImgsNoise :
        if single_view :

            scene_type = theme[themeType] + '_' + 'single_view_' + str(numIms) + '_images'+'_medium_radiance_'+ str(screenParams['maxRadiance']) #'_cloud_for_stats'
        else:
            scene_type = theme[themeType] + '_' + str(numIms) + '_views' 

        save_file_name = scene_name + "_" + resTime + "_" + scene_type     
        save_file_name = scene_name + "_" + resTime + "_" + scene_type #raw_input('Enter file name: ')
        simMode = {'show_scene':show_scene,'show_results':show_results ,'single_view':single_view,'increase_samples': increase_samples, 'save_results':save_results,}
        sceneParams = {'nViews': numIms,'runNo':runNo+1, 'camsRadius': camsRadius, 'camsHeight': camsHeight, 'archAngleSize': archAngleSize,
                       'upDirection': upDirection,'horizon': horizon, 'boundsTranslation': boundsTranslation,
                       'screenTranslation': screenTranslation,'screenParams':screenParams,'renderTime':renderTime}

        if not(os.path.isdir(resultsPath)):
            os.mkdir(resultsPath)        
        scipy.io.savemat(resultsPath + "/" + save_file_name +'_pyCams.mat'  , mdict={'camsLookAtVectors': cams , 'camsParam': params, 
                                                                                     'sceneMitsubaParams': sceneParams,'simMode':simMode})
        scipy.io.savemat(resultsPath + "/" + save_file_name +'_pyImages.mat', {'renderedImagesMitsuba':simIm})
        #scipy.io.savemat(resultsPath + "/" + save_file_name +'_pySceneInfo.mat', mdict = {'scene_info':sceneInfo})

        print resTime, 'scene type:' + scene_type + ' has finished. \nResults are saved at: ', resultsPath
    else:
        print resTime, ' Simulation has finished withouts saving results'


