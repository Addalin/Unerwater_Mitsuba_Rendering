import os, sys

import numpy as np
import mayavi.mlab as mi
import matplotlib.pyplot as plt
import parseVolumeDada as pvd
import miscGeometry as mgo

class Scene(object):
    
    # Constructor
    def __init__(self, boundsFilename , boundsTrans , screenFilename , screenTrans ):
        self.boundsVertices, self.boundsFaces = pvd.ply2Poly(boundsFilename, boundsTrans)
        self.screenVertices, self.screenFaces = pvd.ply2Poly(screenFilename, screenTrans)
        self.screenVertices = self.screenVertices.dot(mgo.rotX(90))
        self.cams = None
        self.lights = None
    
    # Add camera
    def addCam(self,obj):
        if self.cams==None:
            self.cams = obj
        else:
            self.cams = np.vstack((self.cams,obj))
            
    # Add Light
    def addLight(self,obj):
        if self.lights==None:
            self.lights = obj
        else:
            self.lights = np.vstack((self.lights,obj))        

    # Get faces
    def getFaces(self):
        return self.faces
    
    # Get vetecies
    def getVert(self):
        return self.vertex
    
    # Show system
    def showSystem(self,do_show=False,camScale=1.0):
        mi.triangular_mesh(self.boundsVertices[:,0],self.boundsVertices[:,1],self.boundsVertices[:,2],self.boundsFaces)
        mi.triangular_mesh(self.screenVertices[:,0],self.screenVertices[:,1],self.screenVertices[:,2],self.screenFaces)
        
        # Plot cameras
        if self.cams is not None:
            shape_points = camScale * np.array([[0, 0, 0],[1 ,1 ,1],[1 ,-1 ,1],[-1 ,-1 ,1],[-1 ,1 ,1],[1,1,1],[1 ,-1 ,1],[0,0,0],[-1 ,1 ,1],[-1 ,-1 ,1],[0,0,0]])
            for i in range(self.cams.shape[0]):
                self.__plotObj(self.cams[i,:],shape_points,(1,0,0),'Cam'+str(i))
        
        # Plot lights
        if self.lights is not None:
            radius = 1
            base_height = 3
            lamp_ang = np.linspace(0,2*np.pi,50)[:,None]
            base_points = np.hstack( (np.sin(lamp_ang)*radius , np.cos(lamp_ang)*radius ))
            base_points = np.hstack( (base_points , base_height*np.ones([base_points.shape[0],1]) ))
            lamp_ang = np.array([0 , np.pi/2 , np.pi, 3*np.pi/2])[:,None]
            cone_points = np.zeros([np.size(lamp_ang)*2,3])    
            cone_points[1::2,:] = np.hstack( (np.sin(lamp_ang)*radius ,
                                              np.cos(lamp_ang)*radius ,  
                                              base_height * np.ones([cone_points.shape[0]/2,1]))) 
            shape_points = np.vstack((base_points , cone_points ))
            
            for i in range(self.lights.shape[0]):
                self.__plotObj(self.lights[i,:],shape_points,(1,1,0),'Light'+str(i))
        if do_show:        
            mi.show()        

    #  -------------- Private methods --------------        
    
    # Plot objera        
    def __plotObj(self,obj,obj_shape,base_color,obj_name):
        # objera center
        mi.points3d(obj[0],obj[1],obj[2],color=base_color,scale_factor=0.2) 
        mi.text3d(  obj[0],obj[1],obj[2],obj_name,scale=0.3,color=(0,0,0))
        # Transform 
        T,T_inv = mgo.transformLookAt(obj[0:3],obj[3:6],obj[6:9])
        obj_shape = np.dot(T,np.r_[ 
            obj_shape.transpose(),
            np.ones([1,np.shape(obj_shape)[0]])])
        mi.plot3d(obj_shape[0,:],obj_shape[1,:],obj_shape[2,:],tube_radius=None,reset_zoom=False)
       
        
                
    
if __name__=='__main__':
    print 'NBV file'
    scene_name = 'hetvol'
    mitsuba_sim_path = os.environ['MITSUBA_SIM'].replace('\\', '/')
    scene_base_path    = mitsuba_sim_path + '/3D_models'      
    scene = Scene(scene_base_path + scene_name + '/' + scene_name + '.ply')
    cams    = np.array([[7,-6,5, 0,0,0,  0,0,1]])
    lights  = np.array([[3,0,0 , 0,0,0,  0,0,1]])
    scene.addCam(cams)
    scene.addLight(lights)
    scene.showSystem()
    
    print 'end NBV'