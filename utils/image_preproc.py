import numpy as np
import nrrd
from utils.filemanip import split_filename
import os


def cropping(image, mask, prefix=None, size=[86, 80, 86]):

    print('\nStarting raw data and mask cropping...')
    imagePath, imageFilename, imageExt = split_filename(image)
    if prefix is None:
        imageOutname = os.path.join(imagePath, imageFilename+'_cropped')+imageExt
    else:
        imageOutname = os.path.join(imagePath, prefix+'_cropped')+imageExt
    
    _, maskFilename, maskExt = split_filename(mask)
    maskOutname = os.path.join(imagePath, maskFilename+'_cropped')+maskExt
    
    maskData, maskHD = nrrd.read(mask)
    imageData, imageHD = nrrd.read(image)
    
    x, y, z = np.where(maskData==1)
    x_size = np.max(x)-np.min(x)
    y_size = np.max(y)-np.min(y)
    z_size = np.max(z)-np.min(z)
    if size:
        offset_x = (size[0]-x_size)/2
        offset_y = (size[1]-y_size)/2
        offset_z = (size[2]-z_size)/2
        if offset_x < 0 or offset_y < 0 or offset_z < 0:
            raise Exception('Size too small, please increase.')
        if offset_x.is_integer():
            new_x = [np.min(x)-offset_x, np.max(x)+offset_x]
        else:
            new_x = [np.min(x)-(offset_x-0.5), np.max(x)+(offset_x+0.5)]
        if offset_y.is_integer():
            new_y = [np.min(y)-offset_y, np.max(y)+offset_y]
        else:
            new_y = [np.min(y)-(offset_y-0.5), np.max(y)+(offset_y+0.5)]
        if offset_z.is_integer():
            new_z = [np.min(z)-offset_z, np.max(z)+offset_z]
        else:
            new_z = [np.min(z)-(offset_z-0.5), np.max(z)+(offset_z+0.5)]
        new_x = [int(x) for x in new_x]
        new_y = [int(x) for x in new_y]
        new_z = [int(x) for x in new_z]
    else:
        new_x = [np.min(x)-20, np.max(x)+20]
        new_y = [np.min(y)-20, np.max(y)+20]
        new_z = [np.min(z)-20, np.max(z)+20]
    croppedMask = maskData[new_x[0]:new_x[1], new_y[0]:new_y[1],
                           new_z[0]:new_z[1]]
    maskHD['sizes'] = np.array(croppedMask.shape)
    
    croppedImage = imageData[new_x[0]:new_x[1], new_y[0]:new_y[1],
                             new_z[0]:new_z[1]]
    imageHD['sizes'] = np.array(croppedImage.shape)
    
    nrrd.write(imageOutname, croppedImage, header=imageHD)
    nrrd.write(maskOutname, croppedMask, header=maskHD)
    print('Cropping done!\n')
    return imageOutname, maskOutname, np.array(croppedImage.shape)