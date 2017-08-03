import os, sys

"""  mitsubaWrapperLib.py - This lib is used to operate Mitsuba  """ 

mitsuba_path = os.environ['MITSUBA_PATH'].replace('\\', '/')
#mitsuba_path = 'C:/Users/addalin/Mitsuba 0.5.0 64bit/Mitsuba 0.5.0'
#mitsuba_path = '/home/addalin/Softwares/Mitsuba/dist'#'C:/Users/addalin/Mitsuba 0.5.0 64bit/Mitsuba 0.5.0'

sys.path.append(mitsuba_path + '/python/2.7')

# Ensure that Python will be able to find the Mitsuba core libraries
os.environ['PATH'] = mitsuba_path + os.pathsep + os.environ['PATH']

import mitsuba
from mitsuba.core import *
from mitsuba.render import SceneHandler
from mitsuba.render import RenderQueue, RenderJob
from mitsuba.render import Scene
import multiprocessing
#import cv2
import numpy as np


# Each row is a cam & light location in Mitsuba's LookAt format,
# i.e. [Point(position) Point(looking towards) Vector(up direction)].
# For example: [1,2,3,  0,0,0,  0,0,1] is a cam/light positioned at [1 2 3], looking 
# towards [0 0 0] with an up vector of [0,0,1]


class Mitsuba(object):
        
    # Constructor
        def __init__(self, base_path,scene_name,params,screenParams):    

                self.params = params
                self.screenParams = screenParams
                self.light = []
                # Get a reference to the thread's file resolver
                self.fileResolver = Thread.getThread().getFileResolver()
                scenes_path = base_path + '/' + scene_name + '/mitsuba' 
                self.fileResolver.appendPath(scenes_path)
                paramMap = StringMap()
                paramMap['myParameter'] = 'value'
                
                ## Load the scene from an XML file
                self.scene = SceneHandler.loadScene(self.fileResolver.resolve(scene_name + '.xml'), paramMap)
                
                ## Setting & adding emmiters to scene - diffusive screen, created out of multiple sub-screens
                self.SetWideScreen()
                # mitsuba.SetSunSky(np.array([[3, 300,3, 0,0,0, 0,0,1]]))
                # TODO : fix overidin of : self.SetWideScreen(params['screenWidth'] , params['screenHeight'],params['resXScreen'],params['resYScreen'], params['screenZPos'],params['variantRadiance'])                
                self.addSceneLights()
                
                ## Simultaneously rendering multiple versions of a scene
                self.scene.initialize()
                self.scheduler = Scheduler.getInstance()
                ## Start up the scheduling system with one worker per local core
                maxThreads = min(multiprocessing.cpu_count(),40)
                for i in range(0, maxThreads):
                        self.scheduler.registerWorker(LocalWorker(i, 'wrk%i' % i))
                self.scheduler.start()
                
                ## Create a queue for tracking render jobs
                self.queue = RenderQueue()
                self.sceneResID = self.scheduler.registerResource(self.scene)

        # ----------------------SET SUNSKY -----------------------
        def SetSunSky(self, dir_vec, radiance=1):
                pmgr = PluginManager.getInstance()
                obj = pmgr.create({
                    'type' : 'sun',
                    'radiance' : Spectrum(radiance)
                })
                self.light.append(obj)
        
        # ----------------------SET SPOTLIGHT -----------------------
        def SetSpotlight(self, dir_vec):
                pmgr = PluginManager.getInstance()
                obj = pmgr.create({
                    'type' : 'spot',
                    'cutoffAngle' : 40.0,
                    'intensity' : Spectrum(50),
                    'toWorld' : Transform.lookAt(
                        Point( dir_vec[0,0] , dir_vec[0,1] , dir_vec[0,2]),
                        Point( dir_vec[0,3] , dir_vec[0,4] , dir_vec[0,5]),
                        Vector(dir_vec[0,6] , dir_vec[0,7] , dir_vec[0,8])
                    )
                })
                self.light.append(obj)
                                    
        # ----------------------SET SCREEN -----------------------
        def SetRectangleScreen(self, screenPos, radiance, dx, dy):
                """Set a sub-screen (rectangle shape attached to area emitter) at screenPos, with dimentions of [dx X dy],
                With radiance radiance [Watt/(m^2*sr)] """                
                pmgr = PluginManager.getInstance()
                resctScreen = pmgr.create({
                    'type' : 'rectangle',
                    'bsdf': {
                            'type': 'diffuse',
                            'illuminant':Spectrum(1.0)
                            #'reflectance' : Spectrum(0.78) # this is causing peaks noise in the result image - from reflections

                    },
                    'toWorld' : Transform.translate(Vector (screenPos[0], screenPos[1], screenPos[2])) * Transform.rotate (Vector(1, 0,0), 180.0) * Transform .scale(Vector(dx/2, dy/2, 1)),
                    'emitter': {
                            'type': 'constant',#'area',#,'constant',#'area',
                            'radiance':Spectrum(radiance),
                            'samplingWeight':10.0                            
                    }
                   })
                self.light.append(resctScreen)                                    
        # ----------------------SET WIDE SCREEN -----------------------       
        def SetWideScreen(self):
        # TODO : fix SetWideScreen() overriding   
        #def SetWideScreen(self, width = 50.0 , height = 20.0, resX = 1, resY = 1, screenZPos = 2, rand = False):       
                """Set a screen of light at Z = screenZPos, with dimentions of [width X height], containing [resX X resY] sub-surfaces of screens.
                The radiance [Watt/(m^2*sr)] of screeen can be either constant [1] of variant unifomily [0,1] """
                width = self.screenParams['screenWidth']
                height = self.screenParams['screenHeight']
                resX = self.screenParams['resXScreen']
                resY = self.screenParams['resYScreen']
                screenZPos = self.screenParams['screenZPos']
                rand = self.screenParams['variantRadiance']  
                maxRadiance = self.screenParams['maxRadiance']
                
                screenXCorners = width/2* np.array([-1 , 1])
                screenYCorners = height/2*np.array([-1 , 1])
                dx = width / resX
                dy = height / resY
                
                screenX = np.linspace( screenXCorners [0] + dx / 2, screenXCorners [1] - dx / 2, num=resX)
                screenY = np.linspace( screenYCorners [0] + dy / 2, screenYCorners [1] - dy / 2, num=resY)
                for x in screenX:
                        for y in screenY:
                                curRadiance = np.random.uniform(0.0, maxRadiance) if rand else maxRadiance
                                self.SetRectangleScreen( np.array([x, y, screenZPos]), curRadiance, dx, dy)
        #def SetWideScreen(self):
                #"""Set a screen of light at Z = screenZPos, with dimentions of [width X height], containing [resX X resY] sub-surfaces of screens.
                #The radiance [Watt/(m^2*sr)] of screeen can be either constant [1] of variant unifomily [0,1] """
                #width = self.params['screenWidth']
                #height = self.params['screenHeight']
                #resX = self.params['resXScreen']
                #resY = self.params['resYScreen']
                #screenZPos = self.params['screenZPos']
                #rand = self.params['variantRadiance']                
                #self.SetWideScreen() = SetWideScreen(width  , height , resX , resY, screenZPos, rand )        

        # ----------------------SET CAMERA -----------------------
        def SetCamera(self,dir_vec):
                """Create and pre-set a new sensor according to dir_vec""" 
                pmgr = PluginManager.getInstance()
                obj = pmgr.create({
                    'type' : 'perspective',
                    'toWorld' : Transform.lookAt(
                        Point( dir_vec[0,0] , dir_vec[0,1] , dir_vec[0,2]),
                        Point( dir_vec[0,3] , dir_vec[0,4] , dir_vec[0,5]),
                        Vector(dir_vec[0,6] , dir_vec[0,7] , dir_vec[0,8])
                    ),
                    #'focalLength': self.params['focalLength'], # focalLength can be achived by 'fov' & 'fovAxis' 
                    'fov': self.params['fov'],
                    'fovAxis': self.params['fovAxis'],
                    #'farClip':100.0,
                    'film' : {
                        'type' : 'hdrfilm',  #'mfilm',  #'ldrfilm',
                        'width' :  self.params['nWidth'],
                        'height' : self.params['nHeight'],
                    },
                    'sampler' : {
                               'type' :'ldsampler',#'independent',#'ldsampler',
                               'sampleCount' : self.params['sampleCount'],
                               'dimension': self.params['samplerDimention']
                    },
                   'medium' : { # commented out only for debugging - 
                                'type' : 'homogeneous',
                                'id': 'underwater',
                                #'sigmaS' : Spectrum([0.4, 0.3, 0.3]),  #[0.02, 0.02, 0.02]),
                                'sigmaS' : Spectrum([0.0, 0.0, 0.0]),  # for simulations with no scattering bg_sigmaA / cloud_sigmaA /water_sigmaA
                                'sigmaA' : Spectrum([0.45, 0.06, 0.05]),  #[0.3, 0.3, 0.3]),
                                'phase' : {
                                        'type' : 'hg',
                                        'g' : 0.9
                                    }    
                                
                    }                            
                }) 
                self.cam = obj
                
        def createSampler(self,sampleCount):
                pmgr = PluginManager.getInstance()
                obj = pmgr.create({
                    'type' : 'ldsampler',#independent',#'sobol',
                    'sampleCount' : sampleCount,
                    #'sampleCount' : self.params['sampleCount'],
                    # TODO: add function for updating self.params instead of passing them
                    'dimension': self.params['samplerDimention'] #,
                    #'scramble':10 # not sure how this is working yet
                    })
                self.sampler = obj        

        # ----------------------RENDER-----------------------         
        def addSceneLights(self):
                """ Adding all the pre-setted lights to the scene"""
                currScene = Scene(self.scene)
                for light in self.light:
                        currScene.addChild(light)  
                self.scene = currScene
                
        # ----------------------RENDERhjk-----------------------         
        def Render(self,sampleCount,i):
                ## Creating a copy of the base scene and add modifications regarding varaiant camera's properties (sensor position, sampler)
                currScene = Scene(self.scene) 
                currScene.configure()
                pmgr = PluginManager.getInstance()
                currScene.addSensor(self.cam)   
                currScene.setSensor(self.cam) 
                self.createSampler(sampleCount)
                currScene.setSampler(self.sampler) #(self.sampler)
                currScene.setDestinationFile('')
                
                ## Create a render job and insert it into the queue
                #job = RenderJob('myRenderJob'+str(i), currScene, self.queue )
                curSceneResID = self.scheduler.registerResource(currScene)
                job = RenderJob('myRenderJob'+str(i), currScene, self.queue,curSceneResID )
                #job = RenderJob('myRenderJob'+str(i), currScene, self.queue,self.sceneResID )  # passing self.sceneResID - in order to create shallow copy of the scene to all warkers
                job.start()
                
                self.queue.waitLeft(0)
                self.queue.join()
                
                ## Aquire Bitmap format of the rendered image: 
                film = currScene.getFilm()
                size = film.getSize()
                bitmap = Bitmap(Bitmap.ERGBA, Bitmap.EFloat16, size)
                film.develop(Point2i(0, 0), size, Point2i(0, 0), bitmap)
                
                ## End of render - get result
                result_image = np.array(bitmap.buffer()) if sys.platform == 'linux2' else  np.array(bitmap.getNativeBuffer())
                # TODO : update Mitsuba version of Windows, with the updated API - bitmap.getNativeBuffer() doesn't exsists animore                        
                currSceneInfo = currScene.getAABB
                return result_image, currSceneInfo
        
        def shutDownMitsuba(self):
                self.queue.join()
                self.scheduler.stop()