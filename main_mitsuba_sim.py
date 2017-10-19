import os, sys
import numpy as np
import scipy.io
 
import nextBestViewLib as nbv
import matplotlib.pyplot as plt
import mitsubaWrapperLib as mitLib
import miscGeometry as mgo


import yaml
import pandas as pd

from time import gmtime, strftime
import timeit

def conv2nparray(dict_in):
    """converting elements in dictionary from list to np.array"""
    for key in dict_in:
        if type(dict_in[key]) is list:
            dict_in[key] = np.array(dict_in[key])
    return dict_in
        
def configNViews(simMode,sceneParams):
    
    if simMode['single_view'] :
        sceneParams['nRunOp'] = np.array([simMode['nRuns']])
        sceneParams['archAngleSize'] = 0
    else:
        sceneParams['nRunOp'] = np.ones(simMode['nRuns'],dtype=int)*simMode['nViews']
    return sceneParams

def setSimParams (fileName='', sensorName=''):
    """Set simulation parameters"""
    with open(fileName,'r') as ymlfile:
            sim_cfg = yaml.load(ymlfile)
            
    ## SET SIMULATION MODE  
    simMode = sim_cfg['simulation'] 
    sceneType ='bg' if 'bg' in simMode['theme_type'] else 'cloud'
    colors = ['red','green','blue']
    sceneChannel = 'rgb'
    for c in colors:
        if c in simMode['theme_type']:
            sceneChannel = c  
    simMode['theme_type'] = sceneType
    simMode['channel'] = sceneChannel

        
    ## SET CAMERA'S PARAMETERS   
    if sensorName:
        camsParam = sim_cfg['cams'][sensorName]
    else:
        camsParam = sim_cfg['cams']['test1']
    camsParam['samplerDimention'] = 4
    camsParam['sampleCount'] = 1024 # Samlpes per pixel
    camsParam['width'] = camsParam['nWidth']*camsParam['du']
    camsParam['height'] = camsParam['nHeight']*camsParam['dv']
            
    
    ## SET SCREEN PARAMETERS
    screenParams = sim_cfg['screen'] 
    
    ## SET CAMERAS SPACIAL SCENE PARAMETERS
    sceneParams = sim_cfg['scene']
    sceneParams = configNViews(simMode,sceneParams)
        
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
            curIm , sceneInfo = mitsuba.Render(camsParam['sampleCount'],indCam)
            if not(simMode['channel'])=='rgb':
                chan = ['red','green','blue'].index(simMode['channel'])
                curIm = curIm[:,:,chan]
            simIm[indCam] = curIm
                
            currSceneInfo.append(sceneInfo)
            print 'Rendered '+str(indCam + 1)+'/'+str(numIms)
            
        toc = timeit.default_timer()
        runTime = toc - tic # elapsed time in seconds - for a single run 
        print 'Done renderings for iteration run no ' + str(runNo+1)         
    
        ## PLOT RESULT
        if simMode['show_results'] and os.environ['SYS_NAME']!='AWS':
            showResults(simIm,numIms)
            
        ## SAVE RESULT:
        if simMode['save_results']:
            saveResults(simIm, cams, camsParam, sceneParams, simMode,runTime,runNo,startTime)
        else:
            print ' Results were not saves'
                        
    print strftime("%d-%m-%Y_%H-%M-%S", gmtime()) + ' Mituba simulation has finished succesfully'
    mitsuba.shutDownMitsuba()   
    
def showResults(simIm,numIms):
    """Plot rendered images of single run"""
    for indIm, im in enumerate(simIm):
        plt.subplot(1,numIms,indIm+1)
        plt.imshow(im,vmin=0.0,vmax= 1.0)
        plt.axis('off')
    plt.show()
    
def showScene(scene_base_path,scene_name,cams,sceneParams):
    """Show 3D scene"""
    shape_filename   = scene_base_path + '/' + scene_name + '/mitsuba/' + scene_name + '.serialized'
    boundsPLYPath = scene_base_path + '/' + scene_name + '/' + 'bounds' + '.ply'
    screenPLYPath = scene_base_path + '/'  + scene_name + '/' + 'wideScreen' + '.ply'
    scene = nbv.Scene(boundsPLYPath , sceneParams['boundsTranslation'] , screenPLYPath , sceneParams['screenTranslation'])
    scene.addCam(cams)
    #scene.addLight(lights)
    camScale = 0.2
    scene.showSystem(True,camScale)    

def saveResults(simIm, cams, camsParam, sceneParams, simMode,runTime,runNo,startTime):
    """
    Saving images and other parameters of current run
    """
    # Set paths and names
    mitsuba_results_path = os.environ['MITSUBA_RESULTS'].replace('\\', '/')
    resolution_str = str(camsParam['nWidth']) +' X '+str(camsParam['nHeight'])
    resolution_folder = 'resolution '+ resolution_str   
    resolution_folder_path = mitsuba_results_path + '/' + resolution_folder
        
    if simMode['single_view'] :
        views_str = '_single view_' 
    else:
        views_str = '_multiple_' + str(simMode['nViews']) + '_views_'
    
    scene_type = simMode['theme_type'] + '_' + simMode['channel'] + views_str
    scenario_path = scene_type +  str(simMode['nRuns'])+'_runs_'+ startTime 
    resultsPath = resolution_folder_path + '/' + scenario_path  

    resTime = 'run_no_'+str(runNo+1)
    base_file_name = resultsPath + "/" +  scene_type + resTime      
    cams_file_name = base_file_name + '_pyCams.mat'
    imgs_file_name = base_file_name + '_pyImages.mat'

    
    # Create a new results folder
    if not(os.path.isdir(resultsPath)):
        if not(os.path.isdir(resolution_folder_path)):
            os.mkdir(resolution_folder_path)
        os.mkdir(resultsPath)
        append_new_log_line = True
    else:
        append_new_log_line = False

    # save results in mat files
    scipy.io.savemat(cams_file_name, mdict={'camsLookAtVectors': cams , 'camsParam': camsParam,'screenParams':screenParams,
                                            'sceneMitsubaParams': sceneParams,'simMode':simMode,'startTime':startTime,'runTime':runTime})
    scipy.io.savemat(imgs_file_name, {'renderedImagesMitsuba':simIm})
    #scipy.io.savemat(resultsPath + "/" + save_file_name +'_pySceneInfo.mat', mdict = {'scene_info':sceneInfo})

    print 'Results are saved at:\n', resultsPath
    if append_new_log_line:
        log_res_new = {'resolution':resolution_str,       
                   'nViews':simMode['nViews'],           
                   'camera_radius':sceneParams['camsRadius'],  
                   'scene':simMode['theme_type'],            
                   'beta_scale':sceneParams['betaScale'][simMode['theme_type']],       
                   'albedo_bg':sceneParams['albedo']['bg'],        
                   'albedo_theme':sceneParams['albedo']['cloud'],     
                   'matrixA': 'new',          
                   'res_dir':resultsPath,          
                   'recovery_dir':'',     
                   'SparseA_dir':'',      
                   'channel':simMode['channel'],
                   'comments':simMode['comments'] #'New resolution'
                   }
        csvlog_file_name = mitsuba_sim_path + 'results_log.csv'
        log_res_df = pd.read_csv(csvlog_file_name,sep=',',index_col=False)
        log_res_df.fillna(value='',inplace=True)
        log_res_df = log_res_df.append(pd.Series(log_res_new), ignore_index=True)
        log_res_df = log_res_df.sort_values(by=['camera_radius','resolution','nViews','scene'])
        log_res_df.to_csv(csvlog_file_name, sep=",", na_rep='',index=False)
    
    # Load files to s3 -  Amazon bucket
    if (os.environ['SYS_NAME']=='AWS') :
        print 'Coping results to aws bucket @ s3://addaline-data/'
        s3_sim_results = 'mitsuba_sim_results/'+resolution_folder+'/'
        #dist_resultsPath = resolution_folder + '/' + scenario_path
        cmd = 'aws s3 sync "' + resultsPath + '" s3://addaline-data/"' + s3_sim_results + scenario_path +'"'     
        os.system(cmd)
        
        if append_new_log_line:
            cmd = 'aws s3 sync ' + mitsuba_sim_path + ' "s3://addaline-data/' + s3_sim_results + '" --exclude="*" --include="results_log.csv" --include="output*.txt"'        
            os.system(cmd)



if __name__=='__main__':
    import nextBestViewLib as nbv
    print 'main_mitsuba_sim.py'
      
    ## SET SIMULATION PARAMETERS & MITSUBA PATH 
    global mitsuba_sim_path    
    mitsuba_sim_path = os.environ['MITSUBA_SIM'].replace('\\', '/')
    cfgFile = mitsuba_sim_path + '/sim_config.yml'
    sensorName = 'test1' #'test1'#'IMX264'#'test1'#'IMX264'
    
    camsParam, screenParams, sceneParams, simMode = setSimParams (cfgFile,sensorName)
    scene_base_path = mitsuba_sim_path + '/3D_models' 
    scene_name = 'hetvol'
    
    ## RUN SIMULATION:
    for nViews in [3] : #,7,8 -- currently not including 7,8 nViews
        print 'Start simulation for nViews = ' + str(nViews)
        simMode['nViews'] = nViews
        # update nViews 
        sceneParams = configNViews(simMode,sceneParams)
        tic=timeit.default_timer()
        runSimulation(scene_base_path,scene_name,simMode,camsParam,screenParams,sceneParams)
        toc=timeit.default_timer()
        print 'Finished simulation for nViews = ' + str(nViews)
        print 'elapsed time ' + str(toc - tic) + ' sec' #elapsed time in seconds
