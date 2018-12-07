import nibabel as nib
import numpy as np
import glob


def dice_calculation(gt, seg):

    gt = nib.load(gt).get_data() 
    seg = nib.load(seg).get_data() 
    seg = np.squeeze(seg) 
    vox_gt = np.sum(gt) 
    vox_seg = np.sum(seg) 
    common = np.sum(gt & seg) 
    dice = (2*common)/(vox_gt+vox_seg) 
    return dice


def outliers_modified_z_score(ys):

    ys = np.asarray(ys)
    threshold = 3.5

    median_y = np.median(ys)
    median_absolute_deviation_y = np.median([np.abs(y - median_y) for y in ys])
    modified_z_scores = [0.6745 * (y - median_y) / median_absolute_deviation_y
                         for y in ys]
    return np.where(np.abs(modified_z_scores) > threshold)


refs = sorted(glob.glob('/home/fsforazz/Desktop/mouse_nifti/Mask_0*.nii.gz'))
segs = sorted(glob.glob('/home/fsforazz/niftynet/models/mouse_lung_ct/'
                        'segmentation_output_mouse_lung/*.nii.gz'))
all_dices = []

for seg in segs: 
    seg_num = seg.split('/')[-1].split('_')[1] 
    ref = [x for x in refs if seg_num in x][0] 
    dice = dice_calculation(ref, seg) 
    all_dices.append(dice)

outliers = outliers_modified_z_score(all_dices)
print('Mean Dice: {0} \nStd: {1} \nMax Dice: {2}\nMin Dice {3}'
      .format(np.mean(all_dices), np.std(all_dices), np.max(all_dices), np.min(all_dices)))
for ol in outliers[0]:
    print('Outlier: {0}, Dice: {1}'.format(segs[ol], all_dices[ol]))
print('Done!')
