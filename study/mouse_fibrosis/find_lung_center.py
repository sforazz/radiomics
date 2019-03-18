import nibabel as nib
import numpy as np
from scipy.signal import find_peaks
import scipy.ndimage as sn


def peak_calculation(array):
    
    n_peaks = np.inf
    distance = 5
    while n_peaks > 2:
        peaks, _ = find_peaks(array, distance=distance)
        n_peaks = len(peaks)
        distance += 1

    return peaks


def z_coordinate_calculation(mask, x):

    _, z = np.where(mask[x, :, :]==1)
    len_0 = 0
    for el in sorted(list(set(z))):
        y = np.where(mask[x, :, el]==1)[0]
        len_y = np.max(y) - np.min(y)
        if len_y > len_0:
            z_coord = el
            len_0 = len_y
    
    return z_coord


def z_coordinate_calculation_2(mask, x, y):
    
    z = np.where(mask[x, y, :]==1)
    z_min = np.min(z)
    z_max = np.max(z)

    return int(z_min+((z_max-z_min)/2))


def y_coordinate_calculation_2(mask, x):

    y, _ = np.where(mask[x, :, :]==1)
    len_0 = 0
    for el in sorted(list(set(y))):
        z = np.where(mask[x, el, :]==1)[0]
        len_z = np.max(z) - np.min(z)
        if len_z > len_0:
            y_coord = el
            len_0 = len_z
    
    return y_coord

def y_coordinate_calculation(mask, x, z):
    
    y = np.where(mask[x, :, z]==1)
    y_min = np.min(y)
    y_max = np.max(y)

    return int(y_min+((y_max-y_min)/2))


def find_center(index, coord, mask, ax='z'):
    
    x = index[coord]
    if ax == 'z':
        z = z_coordinate_calculation(mask, x)
        y = y_coordinate_calculation(mask, x, z)
    elif ax == 'y':
        y = y_coordinate_calculation_2(mask, x)
        z = z_coordinate_calculation_2(mask, x, y)
    p = [x, y, z]
    
    return p


mask = '/mnt/sdb/mouse_data_prep_new/20WK_RT13_RT+FG+N__A_date_20160323_time_171034.046000/RT13_R_picked_cropped.nii.gz'
mask = nib.load(mask).get_data()
mask = sn.morphology.binary_erosion(mask, structure=np.ones((5, 5, 5))).astype(mask.dtype)

x, y, z = np.where(mask==1)

index_x = sorted(list(set(x)))
len_y = [0]                                                                                                                                                                                                  
len_z = [0]

for i in index_x: 
    xx = np.where(x==i)
    if len(xx[0]) > 1:
        yy = y[np.min(xx):np.max(xx)]
        zz = z[np.min(xx):np.max(xx)] 
        len_z.append(np.max(zz)-np.min(zz)) 
        len_y.append(np.max(yy)-np.min(yy))
    else:
        len_z.append(0) 
        len_y.append(0)

peaks_y = peak_calculation(len_y)-1
peaks_z = peak_calculation(len_z)-1

centers = []
for i in range(2):
    p1 = find_center(index_x, peaks_y[i], mask)
    p2 = find_center(index_x, peaks_z[i], mask, ax='y')
    centers.append([np.round(np.abs(p1[0]+p2[0])/2), np.round(np.abs(p1[1]+p2[1])/2), np.round(np.abs(p1[2]+p2[2])/2)])

print('1st Half Lung center x:{0}, y:{1}, z:{2}'.format(centers[0][0], centers[0][1], centers[0][2]))
print('2nd Half Lung center x:{0}, y:{1}, z:{2}'.format(centers[1][0], centers[1][1], centers[1][2]))
