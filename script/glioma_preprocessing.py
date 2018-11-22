import glob
from utils.filemanip import dcm_info, dcm_check
import os
import shutil
from converters.dicom import DicomConverters
import re
from utils.rt import export_RTS
import argparse


IMAGE_TO_CHECK = ['BPLCT', 'PlanningMRI', 'FUMRI', 'FU_MRI']


def run_preproc(root, tempDir):
    subjects = sorted([os.path.join(root, name) for name in os.listdir(root)
                       if os.path.isdir(os.path.join(root, name))])
    
    for sub in subjects:
        print('\nProcessing subject {}'.format(sub))
        subName = sub.split('/')[-1]
        scans = [x for x in glob.glob(sub+'/*') if os.path.isdir(x) and
                 (x.split('/')[-1] in IMAGE_TO_CHECK
                 or re.match('(R|r)(T|t).*(p|P)(L|l)(A|a)(N|n)', x.split('/')[-1]))]
        for scan in scans:
            scanName = scan.split('/')[-1]
            if scanName == 'FU_MRI':
                scanName = 'FUMRI'
            elif re.match('(R|r)(T|t).*(p|P)(L|l)(A|a)(N|n)', scanName):
                scanName = 'RTPLAN'
            dirName = os.path.join(tempDir, subName, scanName)
            os.makedirs(dirName)
            if scanName in IMAGE_TO_CHECK:
                dicoms, im_types, series_nums = dcm_info(scan)
                dicoms = dcm_check(dicoms, im_types, series_nums)
        
                for f in dicoms:
                    shutil.copy2(f, dirName)
                
                converter = DicomConverters(dirName)
                converter.mitk_converter()
            else:
                try:
                    rtStruct = glob.glob(scan+'/*STRUCT*')[0]
                    shutil.copy2(rtStruct, os.path.join(tempDir, dirName))
                    extract_rt = True
                except IndexError:
                    extract_rt = False
                    print('No RT-STRUCTURE file found in {}'.format(scan))
        if extract_rt:
            missing = export_RTS(os.path.join(tempDir, subName))
            if missing:
                with open(os.path.join(tempDir, 'Missing_contours.txt'), 'a') as f:
                    for m in missing:
                        f.write('Subject {0} misses the {1} contour \n'
                                .format(os.path.join(tempDir, subName), m))


if __name__ == "__main__":
    
#     root = '/home/fsforazz/Desktop/PhD_project/test_data_10-10-18/'
#     tempDir = '/home/fsforazz/Desktop/test_dcm2nrrd2'

    parser = argparse.ArgumentParser()
    parser.add_argument('--root', '-r', type=str)
    parser.add_argument('--output', '-o', type=str)

    args = parser.parse_args()
  
    run_preproc(args.root, args.output)

print('Done!')
