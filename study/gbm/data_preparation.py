from core.utils.dicom import dcm_info, dcm_check
import os
import shutil
from core.converters.dicom import DicomConverter
import argparse
from pathlib import Path


IMAGE_TO_CHECK = ['CT', 'RTSTRUCT', 'T1', 'T1KM', 'T2', 'ADC', 'SWI', 'FLAIR']


def run_preparation(root, tempDir, convert_to='nrrd'):

    root = Path(root)
    tempDir = Path(tempDir)
    subjects = sorted([root/x for x in root.iterdir() if x.is_dir()])
    
    for sub in subjects:
        print('\nProcessing subject {}'.format(sub))
        scans = {}
        subName = sub.parts[-1]
        for im_t in IMAGE_TO_CHECK: 
            scans[im_t] = [x for x in sub.rglob('*.dcm') if x.parts[-5]==im_t and x.parts[-4]=='TRA_or_3D'
                           and x.parts[-3].split('_')[0]=='1']
        for k in scans.keys(): 
            if not scans[k] and k == 'RTSTRUCT': 
                scans[k] = [x for x in sub.rglob('*.dcm') if x.parts[-3]==k] 
            elif not scans[k] and not k == 'RTSTRUCT': 
                scans[k] = [x for x in sub.rglob('*.dcm') if x.parts[-5]==k and x.parts[-3].split('_')[0]=='1']
        
        for k in scans.keys():
            if scans[k] and not k == 'RTSTRUCT':
                series = sorted(list(set([x.parts[-3] for x in scans[k]])))
                if len(series) > 1:
                    imgs = [x for x in scans[k] if x.parts[-3]==series[0]]
                    scans[k] = imgs

        for scan in scans.keys():
            images = scans[scan]
            if images:
                if scan == 'RTSTRUCT':
                    scanName = images[0].parts[-3]
                else:
                    scanName = images[0].parts[-5]
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
