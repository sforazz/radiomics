from core.utils.dicom import dcm_info, dcm_check
import os
import shutil
from core.converters.dicom import DicomConverter
import argparse
from pathlib import Path
import nibabel as nib


IMAGE_TO_CHECK = ['CT', 'RTSTRUCT', 'MR_T1', 'MR_T1KM', 'MR_T2', 'MR_FLAIR']


def run_preparation(root, tempDir, convert_to='nrrd'):

    root = Path(root)
    tempDir = Path(tempDir)
    subjects = sorted([root/x for x in root.iterdir() if x.is_dir()])

    for sub in subjects:
        print('\nProcessing subject {}'.format(sub))
        scans = {}
        subName = sub.parts[-1]
        if not os.path.isdir(tempDir / subName):
            for im_t in IMAGE_TO_CHECK: 
                scans[im_t] = [x for x in sub.rglob('*.dcm') if x.parts[-3]==im_t]
    
            for scan in scans.keys():
                images = scans[scan]
                if images:
                    scanName = images[0].parts[-3]
                    dirName = tempDir / subName / scanName
                    if not os.path.isdir(dirName):
                        os.makedirs(dirName)
                    else:
                        shutil.rmtree(dirName)
                        os.makedirs(dirName)
                    
                    if scan != 'RTSTRUCT':
                        dicoms, im_types, series_nums = dcm_info(images)
                        dicoms = dcm_check(dicoms, im_types, series_nums)
                        for f in dicoms:
                            shutil.copy2(f, dirName)
                        if dicoms:
                            converter = DicomConverter(str(dirName))
                            converter.convert(convert_to=convert_to)
                        else:
                            print('{} folder seems to do not contain any correct DICOM files.'
                                  ' Conversion cannot be made and it will be ignored.'.format(scan))
                    else:
                        for f in images:
                            shutil.copy2(f, dirName)
        else:
            print('Subject already processed. Skipping')
    
    converted_files = [os.path.join(root, name) for root, _, files in os.walk(tempDir)
            for name in files if name.endswith('.nii.gz')]
    to_remove = []
    for f in converted_files:
        ref = nib.load(f)
        data = ref.get_data()
        if len(data.squeeze().shape) == 2 or len(data.squeeze().shape) > 4:
            to_remove.append(f)
        elif len(data.squeeze().shape) == 4:
            im2save = nib.Nifti1Image(data[:, :, :, 0], affine=ref.affine)
            nib.save(im2save, f)
        if len(data.dtype) > 0:
            print('{} is not a greyscale image. It will be removed.'.format(f))
            to_remove.append(f)
    
    if to_remove:
        for f in to_remove:
            os.remove(f)
            


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--root', '-r', type=str)
    parser.add_argument('--output', '-o', type=str)
    parser.add_argument('--convert_to', '-c', type=str, 
                        help='Format for the converted DICOM file. Possible values are: "nrrd", '
                        '"nifti" and "nifti_gz". Default is nrrd.', default='nrrd')

    args = parser.parse_args()
  
    run_preparation(args.root, args.output, convert_to=args.convert_to)

print('Done!')
