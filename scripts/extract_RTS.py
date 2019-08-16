from radiomics.utils.rt import contour_names
import argparse
import os
import glob
import nibabel as nib
import numpy as np
import subprocess as sp
import shutil
import pydicom


if __name__ == "__main__":
 
#     parser = argparse.ArgumentParser()
#     parser.add_argument('--root', '-r', type=str)
#  
#     args = parser.parse_args()
#     subjects = [x for x in os.listdir(args.root) if os.path.isdir(os.path.join(args.root, x))]
    rts = sorted(glob.glob('/mnt/sdb/Cinderella_CONVERTED/*/*/RTSTRUCT/*.dcm'))
    rt = [x.split('RTSTRUCT')[0] for x in rts]
     
    for sub in rt[21:]:
        print('\nProcessing subject: {}'.format(sub))
        reference = os.path.join(sub, 'CT')
        rtstruct = os.path.join(sub, 'RTSTRUCT')
        rt_file = glob.glob(rtstruct+'/*.dcm')[0]
        roi_names = contour_names(pydicom.read_file(rt_file))
        rois = [x for x in roi_names if 'gtv' in x.lower()]
        if rois:
            cmd = 'dcmrtstruct2nii convert -r {0} -d {1} -o {2}/structures -s "{3}"'.format(
                rt_file, reference, sub, ','.join([x for x in rois]))
            sp.check_output(cmd, shell=True)
#         os.mkdir(os.path.join(sub, 'to_delete'))
#         dcms = sorted(glob.glob(sub+'/*/*.dcm'))
#         for d in dcms:
#             shutil.copy2(d, os.path.join(sub, 'to_delete'))
# 
# #     Path = '/mnt/sdb/Cinderella_CONVERTED/11EHHTQH/20130506/test'
#         DicomImage = DicomImagestoData(path=os.path.join(sub, 'to_delete'))
#         contours = []
#         for roi in DicomImage.rois_in_case:
#             if 'gtv' in roi.lower():
#                 contours.append(roi)
#                 print(roi)
#         if contours:
#             ct = os.path.join(sub, "CT")
#             cmd = 'dcm2niix -o {0} -z y -f CT_no_flip {1}'.format(sub, ct)
#             sp.check_output(cmd, shell=True)
#             reference = os.path.join(sub, 'CT_no_flip.nii.gz')
#             DicomImage.get_mask(contours)
#             mask = DicomImage.mask
#             mask = np.swapaxes(mask, 0, 2)
#             ref = nib.load(reference)
#             for i in range(mask.shape[-1]):
#                 im2save = nib.Nifti1Image(mask[:, :, :, i].squeeze(), affine=ref.affine)
#                 nib.save(im2save, os.path.join(sub, contours[i]+'.nii.gz'))
#         shutil.rmtree(os.path.join(sub, 'to_delete'))

    print('Done')
