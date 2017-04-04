import os, sys
import numpy as np
import struct
import plyfile as ply

def vol2data(volFileName):
    """vol2data(): Generates 3d matrix (ndarray) from a binary file modified as .vol type
       Input:  volfilename - .vol file name
       Output: volData - 3D matrix of float representing the voxels values of the object
               boundingBox - bounding box of the object [xmin,ymin,zmin],[xmax,ymax,zmax]
               volSize - size (voxels#) of the 3d volume that represents the object [xsize,ysize,zsize] """
    
    fid = open(volFileName, 'rb')
    # Reading first 48 bytes of volFileName as header , count begins from zero  
    header = fid.read(48)  
    
    # Converting header bytes 8-21 to volume size [xsize,ysize,zsize] , type = I : 32 bit integer
    xsize = struct.unpack("I", bytearray(header[8:12]))[0]   # Bytes 8-11 Number of cells along the X axis 
    ysize = struct.unpack("I", bytearray(header[12:16]))[0]  # Bytes 12-15 Number of cells along the Y axis 
    zsize = struct.unpack("I", bytearray(header[16:20]))[0]  # Bytes 16-19 Number of cells along the Z axis 
    
    volSize = [xsize,ysize,zsize]
    
    # Converting header bytes 24-47 to bounding box [xmin,ymin,zmin],[xmax,ymax,zmax] , type = I : 32 bit integer
      
    minx = struct.unpack("f", bytearray(header[24:28]))[0]
    miny = struct.unpack("f", bytearray(header[28:32]))[0]
    minz = struct.unpack("f", bytearray(header[32:36]))[0]
    
    maxx = struct.unpack("f", bytearray(header[36:40]))[0]    
    maxy = struct.unpack("f", bytearray(header[40:44]))[0]
    maxz = struct.unpack("f", bytearray(header[44:48]))[0]

    boundingBox = ([minx, miny,minz],[maxx, maxy,maxz])

    # Converting data bytes 49-* to a 3D matrix size of [xsize,ysize,zsize] , type = f : 32 bit float   
    data = fid.read()
    num_data = len(data)/4        # number of float number in data
    read_str = 'f'*num_data       # type of string for converting bytes to decimal
    volData = struct.unpack(read_str, bytearray(data))
    volData = np.array(volData)
    volData = volData.reshape([xsize,ysize,zsize])

    fid.close()
    
    return volData, boundingBox , volSize




def ply2Poly(plyFileName, transVec = None):
    """ply2Poly(): retreives polygon's vertices and faces from a Polygon file modified as .ply type, uses plyfile module
       Input:  plyFileName - .ply file name
               transVec - a translation vector type of np.array: [tx, ty, tz] if a translation of the polygon is needed
       Output: vertex - vertex of the polygon, translated with transVec
               faces - ordering of vertices that represent the Polygons' faces"""  
    plydata = ply.PlyData.read(plyFileName)
    vertices = np.stack( (plydata['vertex']['x'],plydata['vertex']['y'],plydata['vertex']['z']) , axis = 1) 
    if transVec != None:
        vertices = vertices + transVec
    faces = plydata['face']['vertex_indices']
    faces = np.array(faces.tolist()) # convert faces to Nx3 array
    return vertices, faces

if __name__=='__main__':
    print '.vol data:'
    #volfilename = 'C:/Users/addalin/Downloads/cbox/cbox/meshes/cbox_luminaire.obj'
    mitsuba_sim_path = os.environ['MITSUBA_SIM'].replace('\\', '/')
    scene_base_path    = mitsuba_sim_path + '/3D_models'
    scene_name = 'hetvol' #'cube_with_texture'
    volfilename = mitsuba_sim_path + '/' + scene_name + '/smoke.vol'
    screenPLYPath = scene_base_path + '/'  + scene_name + '/' + 'screen' + '.ply'
    
    data_vec, bounding_box , sizes = vol2data(volfilename)  
    print 'Volume Bounding box = ',bounding_box
    print 'Volume sizes [x voxels,y voxels,z voxels]  = ', sizes
    
    print '\n.ply data:'

    vertices, faces = ply2Poly(screenPLYPath, [0, 1, 0])
    print 'Polygon vertices = '
    for vertex in vertices:
        print vertex
    print 'Polygon faces = '
    for face in faces:
        print face
    print '\nEnd of parsing file'