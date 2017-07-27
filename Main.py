import os, sys
# import mayavi.mlab as mi
import numpy as np
import scipy.io

# import nextBestViewLib as nbv
import matplotlib.pyplot as plt
import mitsubaWrapperLib as mitLib
import miscGeometry as mgo

from time import gmtime, strftime
import timeit
   
## SET PARAMETERS:

params = {}
params['sampleCount'] = 128 #128 # Samlpes per pixel
params['samplerDimention'] = 1024
params['nWidth']    = 2464#1936 # 2464 # 1936 #400#1936 # 2464 # 800  # 400 # Image width
params['nHeight']   = 2056#1458 # 2056 # 1458 # 2056 # 800  # 400 # Image hight
#params['focalLength'] =  '12'  # focalLength in [mm]
params['fov'] = 39.008129097 #28.0725 #39.008129097 # [derees]
params['fovAxis'] = 'x'
params['sensorName'] =  'IMX264'#'ICX674' #'IMX264' #

#other parameteres just for results savings
params['wellDepth'] = 10361.0 # 15770.0  #[electrons]
params['readNoise'] = 2.0 # 10.0 #[electrons]
params['bitDepth'] = 12
params['du'] = 3.45*(10**-6) # 4.54*(10**-6) #[m]
params['dv'] = 3.45*(10**-6) # 4.54*(10**-6) #[m]
params['width'] = params['nWidth']*params['du']
params['height'] = params['nHeight']*params['dv']

## Set simulation MODES parameteres
show_scene = False
show_results = False 
single_view = False
increase_samples = False
save_results = True
theme = ['background','cloud','cubic','empty_cubic','cubic_water','bg_water','bg_vacuum','cubic_vacuum','bg_sigmaA','cloud_sigmaA','cloud_vacuum','cloud_water','bg_water_green','smoke_test_time']
themeType = 13
## SET screen parameteres
screenTranslation = np.array([0, 2, 0])  # screen behind the target - this translation is for visualization coordinates (not for Mitsuba!!!)
screenParams = {}
screenParams['variantRadiance'] = False
screenParams['screenWidth'] = 50.0
screenParams['screenHeight'] = 20.0
screenParams['resXScreen'] = 200
screenParams['resYScreen'] = 500 
screenParams['screenZPos'] = 2.0
screenParams['maxRadiance'] = 1.2



## SET common camera's parameteres
camsRadius = 3
camsHeight = 0
upDirection = np.array([0.0,0.0,1.0])
horizon = np.array([0.0, 1.0, 0.0])
boundsTranslation = np.array([0.0, 0.0, 0.0])  # target

## SET runing scenarios 
nRuns = 2 #64 #np.ceil(params['wellDepth']/params['sampleCount']).astype(int) # nRuns -  number of runing times for scenario
if single_view:
    nRunOp = np.array([nRuns])
    scenario_path = theme[themeType] + '_single view_' + str(nRuns) +' runs'
else:
    numViews = 6 # numViews - varaing cameras positions   
    nRunOp = np.ones(nRuns,dtype=int)*numViews
    scenario_path = theme[themeType] + '_multiple ' + str(numViews) + ' views_'+str(nRuns) + ' runs'        
    # nRunOp - array size of nRuns, each cell value is numViews; This is for running the scene witn numViews camers X nRuns times     
      
    
## Set folders PATHS:
scene_name = 'hetvol'
startTime = strftime("%d-%m-%Y_%H-%M-%S", gmtime())
mitsuba_sim_path = os.environ['MITSUBA_SIM'].replace('\\', '/')
mitsuba_results_path = os.environ['MITSUBA_RESULTS'].replace('\\', '/')
scene_base_path    = mitsuba_sim_path + '/3D_models'                                  #scene_base_path    = '/home/addalin/mitsuba_sim/3D_models/'
if save_results:
    resolution_folder = 'resolution '+ str(params['nWidth']) +' X '+str(params['nHeight'])   
    resolution_folder_path = mitsuba_results_path + '/' + resolution_folder
    resultsPath = resolution_folder_path + '/' + scenario_path + '_' + startTime
    #resultsPath = mitsuba_sim_path + '/sim_results' + '/' + resolution_folder + '/' + scenario_path + '_' + startTime    # old version             
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
    #xCam   = np.array([-0.5 , -0.25 , 0 ,  0.25 , 0.5])  
    #yCam   = np.array([ -0.55 , -0.55 , -0.55 , -0.55, -0.55])  
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
    simIm =  np.zeros(numIms,dtype=np.object) 
    currSceneInfo = []
    tic=timeit.default_timer()     
    for indCam in range (0,numIms):   
        if not(single_view):
            mitCam = mgo.rotScene2Mitsuba(cams[indCam][None,:]) #mitCam = cams[indCam][None,:]   
        mitsuba.SetCamera(mitCam[None,:])
        if increase_samples:
            # increasing samples count - this is for noise statistics: variance vs. samplesCount; increasing every 10 images 
            params['sampleCount'] = params['sampleCount']*2 if (np.mod(numIms,10)==0 & numIms>1) else params['sampleCount']
        simIm[indCam] , sceneInfo = mitsuba.Render(params['sampleCount'],indCam)
        currSceneInfo.append(sceneInfo)
        print 'Rendered '+str(indCam + 1)+'/'+str(numIms)
    toc = timeit.default_timer()
    renderTime = toc - tic #elapsed time in seconds    
    
    ## PLOT RESULT
    if show_results:
        for indIm, im in enumerate(simIm):
            plt.subplot(1,numIms,indIm+1)
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
            
        base_file_name = resultsPath + "/" + scene_name + "_" + resTime + "_" + scene_type     
        cams_file_name = base_file_name + '_pyCams.mat'
        imgs_file_name = base_file_name + '_pyImages.mat'

        simMode = {'show_scene':show_scene,'show_results':show_results ,'single_view':single_view,'increase_samples': increase_samples, 'save_results':save_results,}
        sceneParams = {'nViews': numIms,'runNo':runNo+1, 'camsRadius': camsRadius, 'camsHeight': camsHeight, 'archAngleSize': archAngleSize,
                       'upDirection': upDirection,'horizon': horizon, 'boundsTranslation': boundsTranslation,
                       'screenTranslation': screenTranslation,'screenParams':screenParams,'renderTime':renderTime}
        
        if not(os.path.isdir(resultsPath)):
            if not(os.path.isdir(resolution_folder_path)):
                os.mkdir(resolution_folder_path)
            os.mkdir(resultsPath)   
            
        scipy.io.savemat(cams_file_name  , mdict={'camsLookAtVectors': cams , 'camsParam': params,'sceneMitsubaParams': sceneParams,'simMode':simMode})
        scipy.io.savemat(imgs_file_name, {'renderedImagesMitsuba':simIm})
        #scipy.io.savemat(resultsPath + "/" + save_file_name +'_pySceneInfo.mat', mdict = {'scene_info':sceneInfo})
        
        print resTime, 'scene type:' + scene_type + ' has finished. \nResults are saved at: ', resultsPath
        
        # Load files to s3 -  Amazon bucket
        if (os.environ['SYS_NAME']=='AWS') :
            dist_folder = resolution_folder + '/' + scenario_path + '_' + startTime
            cmd = 'aws s3 sync "'+ resultsPath + '" s3://addaline-data/"' + dist_folder +'"'     
            os.system(cmd)        
    else:
        print resTime, ' Simulation has finished withouts saving results'

    
