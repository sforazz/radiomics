import numpy as np
import nrrd
from utils.filemanip import split_filename
import os


def cropping(image, mask, prefix=None):
    
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
    croppedMask = maskData[np.min(x)-20:np.max(x)+20, np.min(y)-20:np.max(y)+20,
                           np.min(z)-20:np.max(z)+20]
    maskHD['sizes'] = np.array(croppedMask.shape)
    
    croppedImage = imageData[np.min(x)-20:np.max(x)+20, np.min(y)-20:np.max(y)+20,
                             np.min(z)-20:np.max(z)+20]
    imageHD['sizes'] = np.array(croppedImage.shape)
    
    nrrd.write(imageOutname, croppedImage, header=imageHD)
    nrrd.write(maskOutname, croppedMask, header=maskHD)
    
    return imageOutname, maskOutname