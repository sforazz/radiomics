"Script to run temporal ICA on Cinderella FU"
import glob
import os
import shutil
from datetime import datetime as dd
import numpy as np
import nibabel as nib
from sklearn.decomposition import FastICA
import matplotlib.pyplot as plot
from sklearn.cluster import KMeans
from scipy.signal import find_peaks


def data_preparation(data_dir, reg_dir):

    subs = sorted(glob.glob(data_dir+'/*'))
    tps_dict = {}
    for sub in subs:
        sub_name = sub.split('/')[-1]
        tps = sorted(os.listdir(sub))
        if len(tps) > 3:
            tps_list = ['reference_tp']
            for i in range(1, len(tps)):
                diff = (dd.strptime(tps[i], '%Y%m%d')-dd.strptime(tps[0].split('_')[0], '%Y%m%d')).days
                if diff > 130 and diff < 250 and i == 3:
                    tps_list.append(tps[i])
            if len(tps_list) == 2:
                tps_dict[sub_name] = ['reference_tp'] + [x for x in tps[1:4]]
                tps_dict[sub_name] = [os.path.join(reg_dir, sub_name, x, 'T1KM_bet_resampled.nii.gz')
                                      if x=='reference_tp' else os.path.join(reg_dir, sub_name, x,
                                                                             'T1KM_bet_mapped.nii.gz')
                                      for x in tps_dict[sub_name]]
    return tps_dict


def ICA_calculation(tps_dict, ica_components):

    plot_col = ['b', 'r', 'g']
    tc = []  #ICA time courses
    sm_path = []
    for sub in tps_dict:
        image_paths = tps_dict[sub]
        gtv_path = os.path.join(gtv_dir, sub+'.nii.gz')
        ref = nib.load(gtv_path)
        gtv = ref.get_data()
        x, y, z = np.where(gtv == 1)
        if x.any():
            mat = np.zeros((len(image_paths), x.shape[0]))
            for i, image in enumerate(image_paths):
                data = nib.load(image).get_data()
                mat[i, :] = zscoring_image(data[x, y, z])
            ica = FastICA(n_components=ica_components)
            S_ = ica.fit_transform(mat.T)
            A_ = ica.mixing_
            S_zscored, tc_normalized = zscoring_ica(S_, A_)
            tc.append(tc_normalized.T)
            for c in range(ica_components):
                cluster = np.zeros((gtv.shape))
                outname = sub+'_component_{}.nii.gz'.format(c+1)
                for i in range(x.shape[0]):
                    cluster[x[i], y[i], z[i]] = S_zscored[i, c]
                im2save = nib.Nifti1Image(cluster, affine=ref.affine)
                nib.save(im2save, os.path.join(result_dir, outname))
                sm_path.append(os.path.join(result_dir, outname))
                plot.plot(tc_normalized[:, c], '-{}'.format(plot_col[c]),
                          label='component_{}'.format(c+1))
            plot.legend()
            plot.savefig(os.path.join(result_dir, sub+'_timecourses.png'))
            plot.close()
        else:
            print('Empty gtv for subject {}'.format(sub))

    tc = np.asarray(tc)
    tc = tc.reshape(tc.shape[0]*tc.shape[1], tc.shape[2])
    
    return tc, sm_path


def save_clusters(labels, tc, centroids, sm_path, working_dir, out_prefix=''):

    for cluster_num in list(set(labels)):
        save_dir = os.path.join(working_dir, '{}_cluster_{}'.format(out_prefix, cluster_num))
        if not os.path.isdir(save_dir):
            os.mkdir(save_dir)
        plot.plot(tc[labels==cluster_num].T)
        plot.savefig(os.path.join(save_dir, 'all_tcs.png'))
        plot.close()
        plot.plot(centroids[:, cluster_num])
        plot.savefig(os.path.join(save_dir, 'cluster_centroid_tc.png'))
        plot.close()
        for f in [sm_path[x] for x in np.where(labels == cluster_num)[0]]:
            shutil.copy2(f, save_dir)


def elbow_estimation(array, do_plot=True):

    ssd = []
    K = range(1, array.shape[0])
    for k in K:
        km = KMeans(n_clusters=k)
        km = km.fit(array)
        ssd.append(km.inertia_)
    if do_plot:
        plot.plot(ssd)
        plot.savefig('/home/fsforazz/Desktop/ssd.png')
        plot.close()
    percentage_diff = [((ssd[i-1]-ssd[i])/ssd[i])*100 for i in range(1, len(ssd))]
    peaks, _ = find_peaks(percentage_diff)
    num_clusters = peaks[0]+2

    return num_clusters

def clustering(array, n_clusters):

#     n_clusters = elbow_estimation(array, True)
    est = KMeans(n_clusters)
    est.fit(array)
    labels = est.labels_
    centroids = est.cluster_centers_.T
    return labels, centroids


def normalization(array):

    max_value = max(array.flatten())
    min_value = min(array.flatten())
    array = (array - min_value)/(max_value - min_value)

    return array


def zscoring_image(image):

    image = np.asanyarray(image)
    image = image.astype('float64')
    mns = image.mean()
    sstd = image.std()
    res = (image - mns)/sstd
    return res

def zscoring_ica(sm, tc):

    ica_zscore = np.zeros((sm.shape[0], sm.shape[1])) 
    ica_tc = np.zeros((tc.shape[0], tc.shape[1]))
    for i in range(sm.shape[1]): 
        dt = sm[:, i]-np.mean(sm[:, i]) 
        num = np.mean(dt**3) 
        denom = (np.mean(dt**2))**1.5 
        s = num / denom
        if np.sign(s) == -1: 
            print('Flipping sign of component {}'.format(str(i))) 
            sm[:, i] = -1*sm[:, i]
            tc[:, i] = -1*tc[:, i]
        pc = sm[:, i] 
        vstd = np.linalg.norm(sm[:, i])/np.sqrt(sm.shape[0]-1) 
        if vstd != 0: 
            pc_zscore = sm[:,i]/vstd 
        else: 
            print('Not converting to z-scores as division by zero' 
                  ' warning may occur.')
            pc_zscore = pc 
        ica_zscore[:, i] = pc_zscore
        ica_tc[:, i] = zscoring_image(tc[:, i])

    return ica_zscore, ica_tc


def gl_distribution_calculation(labels, sm_path, tps_dict):

    pdf_info = []
    for cluster_num in list(set(labels)):
        spatial_maps = [sm_path[x] for x in np.where(labels == cluster_num)[0]]
        grey_levels_val = None
        for sm in spatial_maps:
            sub_name = sm.split('/')[-1].split('_')[0]
            ica_map = nib.load(sm).get_data()
            x, y, z = np.where(ica_map >= 1.9)
            ref_path = tps_dict[sub_name][0]
            ref_data = nib.load(ref_path).get_data()
            ref_data = zscoring_image(ref_data)
            gls = ref_data[x, y, z]
            if grey_levels_val is None:
                grey_levels_val = gls
            else:
                grey_levels_val = np.concatenate([grey_levels_val, gls])
        pdf_info.append([np.mean(grey_levels_val), np.std(grey_levels_val)])
    return pdf_info


def tp_0_clustering(image, gtv, pdf_info):

    gtv = nib.load(gtv).get_data()
    x, y, z = np.where(gtv == 1)
    data = nib.load(image).get_data()
    data = zscoring_image(data)
    gtv_data = data[x, y, z]
    cluster = np.zeros((gtv.shape+(len(pdf_info),)))
    for i in range(x.shape[0]):
        z_scores = [(gtv_data[i] - x[0])/x[1] for x in pdf_info]
        index = np.where(np.abs(np.asarray(z_scores)) == np.min(np.abs(z_scores)))[0][0]
        cluster[x[i], y[i], z[i], index] = 1
    for i in range(cluster.shape[-1]):
        outname = image.split('.nii.gz')[0]+'_cluster_{}.nii.gz'.format(i+1)
        im2save = nib.Nifti1Image(cluster[:, :, :, i], affine=nib.load(image).affine)
        nib.save(im2save, outname)
#     for c, cluster in enumerate(pdf_info):
#         mu = cluster[0]
#         sigma = cluster[1]
#         zscore = [(x - mu)/sigma for x in data[x, y, z]]
#         cluster = np.zeros((gtv.shape))
#         outname = image.split('.nii.gz')[0]+'_cluster_{}.nii.gz'.format(c+1)
#         for i in range(x.shape[0]):
#             cluster[x[i], y[i], z[i]] = zscore[i]
#         cluster[np.abs(cluster) > 1.6] = 0
#         cluster[cluster != 0] = 1
#         im2save = nib.Nifti1Image(cluster, affine=nib.load(image).affine)
#         nib.save(im2save, outname)


reg_dir = '/mnt/sdb/Cinderella_FU_seg_reg/seg_reg_preprocessing/T1KM'
gtv_dir = '/mnt/sdb/Cinderella_FU_seg_reg/seg_reg_preprocessing/T1KM_gtv_seg_output'
data_dir = '/mnt/sdb/Cinderella_FU_bet/preprocessing/T1KM'
result_dir = '/mnt/sdb/Cinderella_FU_seg_reg/seg_reg_preprocessing/T1KM_ICA'
gtv = '/mnt/sdb/Cinderella_FU_seg_reg/seg_reg_preprocessing/T1KM_gtv_seg_output/8NV0X2U5.nii.gz'
image = '/mnt/sdb/Cinderella_FU_seg_reg/seg_reg_preprocessing/test_ICA/8NV0X2U5/reference_tp/T1KM_bet_resampled.nii.gz'
ica_components = 3

tps_dict = data_preparation(data_dir, reg_dir)
tc, sm_path = ICA_calculation(tps_dict, ica_components)
np.save(os.path.join(result_dir, 'timecourses.npy'), tc)
with open(os.path.join(result_dir, 'spatial_map_paths.txt'), 'w') as f:
    for el in sm_path:
        f.write(el+'\n')
# tc = np.load(os.path.join(result_dir, 'timecourses.npy'))
# with open(os.path.join(result_dir, 'spatial_map_paths.txt'), 'r') as f:
#     sm_path = [x.strip() for x in f]
# elbow_estimation(tc, do_plot=True)
labels, centroids = clustering(tc, 3)
pdf_info = gl_distribution_calculation(labels, sm_path, tps_dict)
tp_0_clustering(image, gtv, pdf_info)
save_clusters(labels, tc, centroids, sm_path, result_dir)

print('Done!')
