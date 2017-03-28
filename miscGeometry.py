import os, sys
import numpy as np

"""  miscGeometry.py General purpose functions """

def normalize(v):
    norm = np.linalg.norm(v)
    if norm==0:
        norm=np.finfo(v.dtype).eps
    return v/norm

def transformLookAt(p, t, up):
    # p - self object position
    # t - terget object position
    # up - up direction
    dir_vec = normalize(t-p)
    left  = normalize(np.cross(up, dir_vec))
    newUp = np.cross(dir_vec, left)

    T = np.zeros([4,4])
    T[0:3,0]  = left
    T[0:3,1]  = newUp    
    T[0:3,2] = dir_vec
    T[0:3,3] = p
    T[3,3]   = 1.0

    q = np.dot(T.transpose()[:-1,:-1] , p.transpose())
        
    T_inverse = np.zeros([4,4])
    T_inverse[0,0:3] = left
    T_inverse[1,0:3] = newUp    
    T_inverse[2,0:3] = dir_vec
    T_inverse[0:3,3] = -q
    T_inverse[3,3]   = 1.0

    return T, T_inverse

def rotScene2Mitsuba (dir_vec):
    ## Mitsuba axis is rotate 90[degrees] around x axis from nvb.Scene axis
    ### dir_vec =  [origin target up] (1X9) 
    dir_vecs = np.reshape(dir_vec, (3,3), order='F')
    dir_vecs_rot = np.matmul(rotX(90),dir_vecs)
    return np.reshape(dir_vecs_rot, 9 , order='F' )

def calcAngleVectors(u, v):
    '''This function generates the angle between vectos u and v in degrees'''
    uvMul = np.dot(u, v)
    uvNorm = np.linalg.norm(u) * np.linalg.norm(v)
    cosTheta = uvMul / uvNorm
    theta = np.arccos(cosTheta)* 180 / np.pi
    return theta

def rotX(theta):
    '''Return rotation matrix arount x axis with angle size of theta [degrees]'''
    theta = np.deg2rad(theta)
    return np.array([[1 ,        0     ,     0         ], 
                     [0 ,np.cos(theta) , -np.sin(theta)] ,
                     [0 ,np.sin(theta) ,  np.cos(theta)]])
def rotZ(theta):
    '''Return rotation matrix arount z axis with angle size of theta [degrees]'''
    theta = np.deg2rad(theta)
    return np.array([[np.cos(theta), -np.sin(theta), 0 ], 
                     [np.sin(theta), np.cos(theta) , 0 ],
                     [0 ,        0     ,     1         ]])

def setCamToWorldVec ( camsPos , upDirection, target):
    '''Retreives toWorld transform vectors for each camera in camsPos [origin = (self position) , target = (0,0,0), up direction = (0,0,1)] '''

    cams = np.hstack((camsPos , np.zeros(camsPos.shape) + target, np.zeros(camsPos.shape) + upDirection))
    
    return cams    

def createCamsCirc(numViews , radius , camHeight , upDirection , target, archAngleSize = 360, horizon = np.array([0, 1, 0])):
    '''This function creates an arch or circle path of camera's positionsm, such that:
       center of path is at (0,0,0), with raduis size. each of numViews cameras are perpendicular to XY plane at z = camHeight
       size of arch angle is defined by archAngleSize, and it's center is looking towords the horizon'''
    
    archRatio = np.float(archAngleSize) / 360
    theta   = np.linspace( 0 , archRatio * 360, numViews )
    axisX = np.array([1, 0, 0])
    lookingAngle = calcAngleVectors(horizon,axisX )
    
    #  Rotating arche's center - looking towords the horizon
    archCenterAngle = 180 + lookingAngle  
    curCenter = np.median(theta)
    #if rotateArch == 0:
        #rotate2center = center - curCenter
    #else:
        #rotate2center = rotateArch - curCenter -  center
    rotate2center = archCenterAngle - curCenter - lookingAngle  
    theta =  np.deg2rad(theta + rotate2center)
    
    # Calculate cameras positions
    xCam   = radius * np.sin(theta)
    yCam   = radius * np.cos(theta)
    zCam   = camHeight * np.ones(numViews)
    
    # Retreives numViews of toWorld transform vectors for each camera [self position, target = (0,0,0), up direction = (0,0,1)]
    camsPos = np.vstack( ( xCam , yCam , zCam ) ).transpose()
    cams =  setCamToWorldVec (camsPos , upDirection, target)
    #cams = np.hstack((camsPos , np.zeros(camsPos.shape) + target, np.zeros(camsPos.shape) + upDirection))
    
    return cams

def makePolygonPath(space_between_vert,xyz_vec,looking_dir,up_dir):
    t = np.linspace(0 , 1, space_between_vert+1)[:,None]
    t = t[0:-1]
 
    xyz_cam = np.empty((0,3))
    for row in range(xyz_vec.shape[0]-1):
        curr_vec = (1-t)*np.tile(xyz_vec[row][None,:],(space_between_vert,1)) + t *np.tile(xyz_vec[row+1][None,:],(space_between_vert,1))
        #print curr_vec 
        xyz_cam = np.vstack((xyz_cam,curr_vec))
    
    cams    = np.hstack((xyz_cam,xyz_cam +looking_dir,np.zeros(xyz_cam.shape) + up_dir)) 
    return cams


def makeCircPath(num_images,radius,z):
    
    theta   = np.linspace(0 , 2*np.pi, num_images+1)
    theta   = theta[0:-1]
    x_cam   = radius * np.sin(theta)
    y_cam   = radius * np.cos(theta)
    
    cams    = np.vstack((x_cam,y_cam)).transpose()
    cams    = np.hstack((cams,
        z*np.ones([cams.shape[0],1]),
        np.zeros([cams.shape[0],5]),
        np.ones([cams.shape[0],1])
        ))   
    
    return cams


    
# DEBUG -----------------------------
if __name__=='__main__':
    cam   = np.array([[7,-6,5], [0,0,0], [0,0,1]])
    T, T_inverse = transformLookAt(cam[0],cam[1],cam[2])
    
    print T
    print T_inverse
    