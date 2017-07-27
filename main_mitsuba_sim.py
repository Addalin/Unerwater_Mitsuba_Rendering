import os, sys
import numpy as np
import scipy.io

import mitsubaWrapperLib as mitLib
import miscGeometry as mgo
import matplotlib.pyplot as plt

from time import gmtime, strftime
import timeit

def setSimParams (simMode):
    """Set simulation parameters"""
        
    camsParam = {}
    camsParam['sampleCount'] = 128 #128 # Samlpes per pixel
    camsParam['samplerDimention'] = 1024
    camsParam['nWidth']    = 100#1936 # 2464 # 1936 #400#1936 # 2464 # 800  # 400 # Image width
    camsParam['nHeight']   = 100#1458 # 2056 # 1458 # 2056 # 800  # 400 # Image hight
    #camsParam['focalLength'] =  '12'  # focalLength in [mm]
    camsParam['fov'] = 39.008129097 #28.0725 #39.008129097 # [derees]
    camsParam['fovAxis'] = 'x'
    camsParam['sensorName'] =  'IMX264'#'ICX674' #'IMX264' #
    
    #other parameteres just for results savings
    camsParam['wellDepth'] = 10361.0 # 15770.0  #[electrons]
    camsParam['readNoise'] = 2.0 # 10.0 #[electrons]
    camsParam['bitDepth'] = 12
    camsParam['du'] = 3.45*(10**-6) # 4.54*(10**-6) #[m]
    camsParam['dv'] = 3.45*(10**-6) # 4.54*(10**-6) #[m]
    camsParam['width'] = camsParam['nWidth']*camsParam['du']
    camsParam['height'] = camsParam['nHeight']*camsParam['dv']
    
    
    ## SET screen parameteres
    screenParams = {}
    screenParams['variantRadiance'] = False
    screenParams['screenWidth'] = 50.0
    screenParams['screenHeight'] = 20.0
    screenParams['resXScreen'] = 200
    screenParams['resYScreen'] = 500 
    screenParams['screenZPos'] = 2.0
    screenParams['maxRadiance'] = 1.2
    
    
    
    ## SET common camera's parameteres
    sceneParams = {}  
    sceneParams['camsRadius'] = 3
    sceneParams['camsHeight'] = 0
    sceneParams['upDirection'] = np.array([0.0,0.0,1.0])
    sceneParams['horizon'] = np.array([0.0, 1.0, 0.0])
    sceneParams['boundsTranslation'] = np.array([0.0, 0.0, 0.0])  # target
    sceneParams['screenTranslation'] = np.array([0, 2, 0])  # screen behind the target - this translation is for visualization coordinates (not for Mitsuba!!!)
    
    ## SET runing scenarios 
    if simMode['single_view'] :
        sceneParams['nRunOp'] = np.array([simMode['nRuns']])
        sceneParams['archAngleSize'] = 0
    else:
        sceneParams['nRunOp'] = np.ones(simMode['nRuns'],dtype=int)*simMode['nViews']
        sceneParams['archAngleSize'] = 125              

    
    return camsParam, screenParams, sceneParams

def runSimulation(scene_base_path,scene_name,simMode,camsParam,screenParams,sceneParams):
    
    startTime = strftime("%d-%m-%Y_%H-%M-%S", gmtime())
    print startTime + ' Start running Mitsuba simulation'
    
    ## LOAD MITSUBA SCENE & ADD LIGHTS SOURCES
    mitsuba = mitLib.Mitsuba(scene_base_path,scene_name,camsParam,screenParams)
    
    for runNo,numIms in enumerate(sceneParams['nRunOp']):
    
        ## SET CAMERA'S POSITIONS (on arch)
        cams = mgo.createCamsCirc(numIms , sceneParams )
    
        ## BUILD AND SHOW SCENE
        if simMode['show_scene']:
            showScene(scene_base_path,scene_name,cams,sceneParams)   
    
        
        simIm =  np.zeros(numIms,dtype=np.object)  # output images
        currSceneInfo = []
        
        ## RUN MITUSBA - FOR EACH CAMERA POSITION
        print 'Start renderings for iteration run no ' + str(runNo+1) 
        tic = timeit.default_timer()       
        for indCam in range (0,numIms): 
            
            ## ADD CURRNET CAMERA TO SCENE  
            if simMode['single_view'] :
                cam = cams[0][None,:]
            else:
                cam = cams[indCam][None,:]    
            mitCam = mgo.rotScene2Mitsuba(cam)   
            mitsuba.SetCamera(mitCam[None,:])
            if simMode['increase_samples']: # increasing samples count - this is for noise statistics: variance vs. samplesCount; increasing every 10 images
                camsParam['sampleCount'] = camsParam['sampleCount']*2 if (np.mod(numIms,10)==0 & numIms>1) else camsParam['sampleCount']
             
            ## RENDER SCENE    
            simIm[indCam] , sceneInfo = mitsuba.Render(camsParam['sampleCount'],indCam)
            currSceneInfo.append(sceneInfo)
            print 'Rendered '+str(indCam + 1)+'/'+str(numIms)
            
        toc = timeit.default_timer()
        runTime = toc - tic # elapsed time in seconds - for a single run 
        print 'Done renderings for iteration run no ' + str(runNo+1)         
    
        ## PLOT RESULT
        if simMode['show_results']:
            showResults(simIm,numIms)
            
        ## SAVE RESULT:
        if simMode['save_results']:
            saveResults(simIm, cams, camsParam, sceneParams, simMode,runTime,runNo,startTime)
        else:
            print ' Results were not saves'
                        
    print strftime("%d-%m-%Y_%H-%M-%S", gmtime()) + ' Mituba simulation has finished succesfully'
        
def showResults(simIm,numIms):
    """Plot rendered images of single run"""
    for indIm, im in enumerate(simIm):
        plt.subplot(1,numIms,indIm+1)
        plt.imshow(im,vmin=0.0,vmax= 1.0)
        plt.axis('off')
    plt.show()
    
def showScene(scene_base_path,scene_name,cams,sceneParams):
    """Show 3D scene"""
    # TODO : Fix NVB library
    shape_filename   = scene_base_path + '/' + scene_name + '/mitsuba/' + scene_name + '.serialized'
    boundsPLYPath = scene_base_path + '/' + scene_name + '/' + 'bounds' + '.ply'
    screenPLYPath = scene_base_path + '/'  + scene_name + '/' + 'wideScreen' + '.ply' 
    scene = nbv.Scene(boundsPLYPath , sceneParams['screenTranslation'] , screenPLYPath , sceneParams['screenTranslation'])
    scene.addCam(cams)
    #scene.addLight(lights)
    camScale = 0.2
    scene.showSystem(True,camScale)    

def saveResults(simIm, cams, camsParam, sceneParams, simMode,runTime,runNo,startTime):
    """
    Saving images and other parameters of current run
    """
    mitsuba_results_path = os.environ['MITSUBA_RESULTS'].replace('\\', '/')
    resolution_folder = 'resolution '+ str(camsParam['nWidth']) +' X '+str(camsParam['nHeight'])   
    resolution_folder_path = mitsuba_results_path + '/' + resolution_folder
        
    if simMode['single_view'] :
        views_str = '_single view_' 
    else:
        views_str = '_multiple_' + str(simMode['nViews']) + '_views_'
    
    scene_type = simMode['theme_type'] + views_str
    scenario_path = scene_type +  str(simMode['nRuns'])+'_runs_'+ startTime 
    resultsPath = resolution_folder_path + '/' + scenario_path  

    resTime = 'run_no_'+str(runNo+1)
    base_file_name = resultsPath + "/" +  scene_type + resTime      
    cams_file_name = base_file_name + '_pyCams.mat'
    imgs_file_name = base_file_name + '_pyImages.mat'

    if not(os.path.isdir(resultsPath)):
        if not(os.path.isdir(resolution_folder_path)):
            os.mkdir(resolution_folder_path)
        os.mkdir(resultsPath)   

    scipy.io.savemat(cams_file_name, mdict={'camsLookAtVectors': cams , 'camsParam': camsParam,
                                            'sceneMitsubaParams': sceneParams,'simMode':simMode,'startTime':startTime,'runTime':runTime})
    scipy.io.savemat(imgs_file_name, {'renderedImagesMitsuba':simIm})
    #scipy.io.savemat(resultsPath + "/" + save_file_name +'_pySceneInfo.mat', mdict = {'scene_info':sceneInfo})

    print 'Results are saved at:\n', resultsPath

    # Load files to s3 -  Amazon bucket
    if (os.environ['SYS_NAME']=='AWS') :
        print 'Coping results to aws bucket @ s3://addaline-data/'
        dist_resultsPath = resolution_folder + '/' + scenario_path
        cmd = 'aws s3 sync "'+ resultsPath + '" s3://addaline-data/"' + dist_resultsPath +'"'     
        os.system(cmd)                


if __name__=='__main__':
    
    print 'main_mitsuba_sim.py'
    
    ## SET SIMULATION MODE
    theme = ['background','cloud','cubic','empty_cubic','cubic_water','bg_water','bg_vacuum',
             'cubic_vacuum','bg_sigmaA','cloud_sigmaA','cloud_vacuum','cloud_water','bg_water_green','smoke_test_time']
    themeType = 13  
    nRuns = 1  # number of runing times per scenario
    nViews = 1 # numViews - varaing cameras positions 
    simMode = {'show_scene':False,'show_results':True ,'single_view':False,
               'increase_samples': False, 'save_results':True,
               'theme_type':theme[themeType],'nRuns':nRuns,'nViews':nViews}  
    
    ## SET MITSUBA PATH & SIMULATION PARAMETERS
    scene_base_path = os.environ['MITSUBA_SIM'].replace('\\', '/') + '/3D_models' 
    scene_name = 'hetvol'
    camsParam, screenParams, sceneParams = setSimParams (simMode)
    
    ## RUN SIMULATION:
    runSimulation(scene_base_path,scene_name,simMode,camsParam,screenParams,sceneParams)    