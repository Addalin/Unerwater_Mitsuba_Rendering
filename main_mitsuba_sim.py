import os, sys
import numpy as np
import scipy.io
import yaml

import mitsubaWrapperLib as mitLib
import miscGeometry as mgo
import matplotlib.pyplot as plt

from time import gmtime, strftime
import timeit

def conv2nparray(dict_in):
    """converting elements in dictionary from list to np.array"""
    for key in dict_in:
        if type(dict_in[key]) is list:
            dict_in[key] = np.array(dict_in[key])
    return dict_in
        
def setSimParams (fileName='', sensorName=''):
    """Set simulation parameters"""
    with open(fileName,'r') as ymlfile:
            sim_cfg = yaml.load(ymlfile)
            
    ## SET SIMULATION MODE  
    simMode = sim_cfg['simulation']   

        
    ## SET CAMERA'S PARAMETERS   
    if sensorName:
        camsParam = sim_cfg['cams'][sensorName]
    else:
        camsParam = sim_cfg['cams']['test1']
    camsParam['samplerDimention'] = 1024
    camsParam['sampleCount'] = 128
    camsParam['width'] = camsParam['nWidth']*camsParam['du']
    camsParam['height'] = camsParam['nHeight']*camsParam['dv']
            
    
    ## SET SCREEN PARAMETERS
    screenParams = sim_cfg['screen'] 
    
    ## SET CAMERAS SPACIAL SCENE PARAMETERS
    sceneParams = sim_cfg['scene']
    if simMode['single_view'] :
        sceneParams['nRunOp'] = np.array([simMode['nRuns']])
        sceneParams['archAngleSize'] = 0
    else:
        sceneParams['nRunOp'] = np.ones(simMode['nRuns'],dtype=int)*simMode['nViews']
        sceneParams['archAngleSize'] = 125 
        
    return camsParam, screenParams, sceneParams, simMode

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
      
    ## SET SIMULATION PARAMETERS & MITSUBA PATH 
    mitsuba_sim_path = os.environ['MITSUBA_SIM'].replace('\\', '/')
    cfgFile = mitsuba_sim_path + '/sim_config.yml'
    sensorName = 'test1'#'IMX264'
    
    camsParam, screenParams, sceneParams, simMode = setSimParams (cfgFile,sensorName)
    scene_base_path = mitsuba_sim_path + '/3D_models' 
    scene_name = 'hetvol'
    
    ## RUN SIMULATION:
    runSimulation(scene_base_path,scene_name,simMode,camsParam,screenParams,sceneParams)    