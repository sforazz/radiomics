import glob
from radiomics.utils.filemanip import dcm_info, dcm_check
import os
import shutil
from radiomics.converters.dicom import DicomConverters
import re
import argparse


IMAGE_TO_CHECK = ['BPLCT', 'PlanningMRI', 'FUMRI', 'FU_MRI']


def run_preparation(root, tempDir):
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
                except IndexError:
                    print('No RT-STRUCTURE file found in {}'.format(scan))


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--root', '-r', type=str)
    parser.add_argument('--output', '-o', type=str)

    args = parser.parse_args()
  
    run_preparation(args.root, args.output)

print('Done!')
