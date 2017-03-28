import os, sys

"""  mitsubaWrapperLib.py - This lib is used to operate Mitsuba  """ 

mitsuba_path = 'C:/Users/addalin/Mitsuba 0.5.0 64bit/Mitsuba 0.5.0'
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
        def __init__(self, base_path,scene_name,params):    

                self.params = params
                self.light = []
                # Get a reference to the thread's file resolver
                self.fileResolver = Thread.getThread().getFileResolver()
                scenes_path = base_path + '/' + scene_name + '/mitsuba' 
                self.fileResolver.appendPath(scenes_path)
                paramMap = StringMap()
                paramMap['myParameter'] = 'value'
                # Load the scene from an XML file
                self.scene = SceneHandler.loadScene(self.fileResolver.resolve(scene_name + '.xml'), paramMap)

                self.scheduler = Scheduler.getInstance()
                # Start up the scheduling system with one worker per local core
                for i in range(0, multiprocessing.cpu_count()):
                        self.scheduler.registerWorker(LocalWorker(i, 'wrk%i' % i))
                self.scheduler.start()
                # Create a queue for tracking render jobs
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
                #self.light = obj
        
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
#                self.light = obj
                                    
        # ----------------------SET SCREEN -----------------------
        def SetRectangleScreen(self, screenPos, radiance, dx, dy):
                pmgr = PluginManager.getInstance()
                resctScreen = pmgr.create({
                    'type' : 'rectangle',
                    'bsdf': {
                            'type': 'diffuse',
                            'reflectance' : Spectrum(0.78)

                    },
                    'toWorld' : Transform.translate(Vector (screenPos[0], screenPos[1], screenPos[2])) * Transform.rotate (Vector(1, 0,0), 180.0) * Transform .scale(Vector(dx / 2, dy / 2, 1)),
                    'emitter': {
                            'type': 'area',
                            'radiance': Spectrum(radiance)
                    }
                   })
                self.light.append(resctScreen)                                    
        # ----------------------SET WIDE SCREEN -----------------------
        def SetWideScreen(self, width = 50.0 , height = 20.0, resX = 1, resY = 1, distance = 2, rand = False):
                screenXCorners = width/2* np.array([-1 , 1])
                screenYCorners = height/2*np.array([-1 , 1])
                dx = width / resX
                dy = height / resY
                
                screenX = np.linspace( screenXCorners [0] + dx / 2, screenXCorners [1] - dx / 2, num=resX)
                screenY = np.linspace( screenYCorners [0] + dy / 2, screenYCorners [1] - dy / 2, num=resY)
                for x in screenX:
                        for y in screenY:
                                curRadiance = np.random.uniform(0.0, 1.0) if rand else 1.0
                                self.SetRectangleScreen( np.array([x, y, distance]), curRadiance, dx, dy)

        # ----------------------SET CAMERA -----------------------
        def SetCamera(self,dir_vec):
                pmgr = PluginManager.getInstance()
                obj = pmgr.create({
                    'type' : 'perspective',
                    'toWorld' : Transform.lookAt(
                        Point( dir_vec[0,0] , dir_vec[0,1] , dir_vec[0,2]),
                        Point( dir_vec[0,3] , dir_vec[0,4] , dir_vec[0,5]),
                        Vector(dir_vec[0,6] , dir_vec[0,7] , dir_vec[0,8])
                    ),
                    #'focalLength': self.params['focalLength'],
                    'fov': self.params['fov'],
                    'fovAxis': self.params['fovAxis'],                    
                    'film' : {
                        'type' : 'hdrfilm',  #'mfilm',  #'ldrfilm',
                        'width' :  self.params['camWidth'],
                        'height' : self.params['camHeight'],
                    },
                    'sampler' : {
                               'type' :'ldsampler',
                               'sampleCount' : self.params['sampleCount']
                    },
                   'medium' : {
                                'type' : 'homogeneous',
                                'id': 'underwater',
                                'scale': 0.5, 
                                'sigmaS' : Spectrum([0.4, 0.3, 0.3]),  #[0.02, 0.02, 0.02]),
                                'sigmaA' : Spectrum([0.45, 0.06, 0.05]),  #[0.3, 0.3, 0.3]),
                                #'thikness': 1, 
                                'phase' : {
                                        'type' : 'hg',
                                        'g' : 0.9
                                    }    
                                
                    }                            
                }) 
                self.cam = obj
                
        def __createSampler(self,sampleCount):
                pmgr = PluginManager.getInstance()
                obj = pmgr.create({
                    'type' : 'ldsampler',  #'independent',
                    'sampleCount' : sampleCount 
                    })
                self.sampler = obj                
                
                
        # ----------------------RENDER-----------------------         
        def Render(self,sampleCount):
                currScene = Scene(self.scene)
                for light in self.light:
                        currScene.addChild(light)
                currScene.configure()    
                currScene.addSensor(self.cam)   
                currScene.setSensor(self.cam) 
                self.__createSampler(sampleCount) # sample count
                currScene.setSampler(self.sampler)
             
                currScene.setDestinationFile('')
                # Create a render job and insert it into the queue
                job = RenderJob('myRenderJob', currScene, self.queue )
                job.start()
                self.queue.waitLeft(0)
                self.queue.join()
                
                film = currScene.getFilm()
                size = film.getSize()
                bitmap = Bitmap(Bitmap.ERGBA, Bitmap.EFloat16, size)
                film.develop(Point2i(0, 0), size, Point2i(0, 0), bitmap)
                # End of render - get result
                result_image = np.array(bitmap.getNativeBuffer())                                
                currSceneInfo = currScene.getAABB
                return result_image, currSceneInfo