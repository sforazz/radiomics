import nibabel as nib
import numpy as np
import os
import nrrd
import collections
import csv
import matplotlib.pyplot as plot


# refs = sorted(glob.glob('/home/fsforazz/Desktop/mouse_nifti/Mask_0*.nii.gz'))
# segs = sorted(glob.glob('/home/fsforazz/Desktop/mouse_segmentation_results/best_network_results/*.nii.gz'))
with open('/home/fsforazz/Desktop/all_refs.txt', 'r') as f:
    refs = [x.strip() for x in f]
with open('/home/fsforazz/Desktop/all_cnns.txt', 'r') as f:
    segs = [x.strip() for x in f]

results = collections.defaultdict(dict)
for i, ref in enumerate(refs):
    rm_path, rm_name = os.path.split(ref)
    im_name = rm_name.split('.')[0].split('_ref_lung')[0]
    results[im_name] = {}
    im_path = os.path.join(rm_path, im_name)
    _, hd = nrrd.read(im_path+'.nrrd')
    size_x, size_y, size_z = [hd['space directions'][0][0],
                              hd['space directions'][1][1],
                              hd['space directions'][2][2]]
    voxel_vol = size_x*size_y*size_z
    image = nib.load(im_path+'.nii.gz').get_data()
    ref_mask = nib.load(ref).get_data()
    cnn_mask = nib.load(segs[i]).get_data()
    x_ref, y_ref, z_ref = np.where(ref_mask==1)
    x_cnn, y_cnn, z_cnn = np.where(cnn_mask==1)
    results[im_name]['mean_ref'] = np.mean(image[x_ref, y_ref, z_ref])
    results[im_name]['mean_cnn'] = np.mean(image[x_cnn, y_cnn, z_cnn])
    results[im_name]['mean_err'] = ((results[im_name]['mean_ref'] - results[im_name]['mean_cnn'])
                                   /results[im_name]['mean_ref'])*100
    results[im_name]['std_ref'] = np.std(image[x_ref, y_ref, z_ref])
    results[im_name]['std_cnn'] = np.std(image[x_cnn, y_cnn, z_cnn])
    results[im_name]['vol_ref'] = x_ref.shape[0]*voxel_vol
    results[im_name]['vol_cnn'] = x_cnn.shape[0]*voxel_vol
    results[im_name]['vol_err'] = ((results[im_name]['vol_ref'] - results[im_name]['vol_cnn'])
                                   /results[im_name]['vol_ref'])*100

fields = ['mouse', 'mean_ref', 'mean_cnn', 'mean_err', 'std_ref', 'std_cnn', 'vol_ref', 'vol_cnn', 'vol_err']

mean_ref = np.asarray([results[x]['mean_ref'] for x in results.keys()])
mean_cnn = np.asarray([results[x]['mean_cnn'] for x in results.keys()])
vol_ref = np.asarray([results[x]['vol_ref'] for x in results.keys()])
vol_cnn = np.asarray([results[x]['vol_cnn'] for x in results.keys()])

err_mean = ((mean_ref-mean_cnn)/mean_ref)*100
err_vol = ((vol_ref-vol_cnn)/mean_ref)*100

with open('/home/fsforazz/Desktop/results_cheng.csv', 'w') as csv_file:
    w = csv.DictWriter(csv_file, fields)
    w.writeheader()
    for k in results:
        w.writerow({field: results[k].get(field) or k for field in fields})

print('Done!')
