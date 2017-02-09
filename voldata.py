import os, sys
import numpy as np
import struct

def vol2data(volfilename):
    ## Generates 3d matrix (ndarray) from a .vol file 
    ## Input:  volfilename - .vol file name
    ## Output: data        - 3D matrix of double/single 
    
    fid = open(volfilename, 'rb')
    # Reading first 48 bytes of volfilename as header , count begins from zero  
    header = fid.read(48)  
    
    # Converting header bytes 8-21 to volume size [xsize,ysize,zsize] , type = I : 32 bit integer
    xsize = struct.unpack("I", bytearray(header[8:12]))[0]   # Bytes 8-11 Number of cells along the X axis 
    ysize = struct.unpack("I", bytearray(header[12:16]))[0]  # Bytes 12-15 Number of cells along the Y axis 
    zsize = struct.unpack("I", bytearray(header[16:20]))[0]  # Bytes 16-19 Number of cells along the Z axis 
    
    sizes = [xsize,ysize,zsize]
    
    # Converting header bytes 24-47 to bounding box [xmin,ymin,zmin],[xmax,ymax,zmax] , type = I : 32 bit integer
      
    minx = struct.unpack("f", bytearray(header[24:28]))[0]
    miny = struct.unpack("f", bytearray(header[28:32]))[0]
    minz = struct.unpack("f", bytearray(header[32:36]))[0]
    
    maxx = struct.unpack("f", bytearray(header[36:40]))[0]    
    maxy = struct.unpack("f", bytearray(header[40:44]))[0]
    maxz = struct.unpack("f", bytearray(header[44:48]))[0]

    bounding_box = ([minx, miny,minz],[maxx, maxy,maxz])

    # Converting data bytes 49-* to a 3D matrix size of [xsize,ysize,zsize] , type = f : 32 bit float   
    data = fid.read()
    num_data = len(data)/4        # number of float number in data
    read_str = 'f'*num_data       # type of string for converting bytes to decimal
    data_vec = struct.unpack(read_str, bytearray(data))
    data_vec = np.array(data_vec)
    data_vec = data_vec.reshape([xsize,ysize,zsize])

    fid.close()
    
    return data_vec, bounding_box , sizes



if __name__=='__main__':
    print 'Volume data file file'
    volfilename =r'C:\Users\addalin\mitsuba_sim\3D_models\hetvol\smoke.vol'    
    data_vec, bounding_box , sizes = vol2data(volfilename)  
    print 'Volume Bounding box = ',bounding_box
    print 'Volume sizes [x voxels,y voxels,z voxels]  = ', sizes
    
    print 'd'