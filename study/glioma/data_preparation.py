import glob
from Radiomics.utils.filemanip import dcm_info, dcm_check
import os
import shutil
from Radiomics.converters.dicom import DicomConverters
import re
import argparse


IMAGE_TO_CHECK = ['BPLCT', 'PlanningMRI', 'FUMRI', 'FU_MRI']


def run_preparation(root, tempDir, convert_to='nrrd'):

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
                if convert_to == 'nrrd':
                    converter.mitk_converter()
                elif convert_to == 'nifti_gz':
                    converter.dcm2niix_converter()
                elif convert_to == 'nifti':
                    converter.dcm2niix_converter(compress=False)
                else:
                    raise Exception('Conversion from DICOM to {} is not supported.'
                                    .format(convert_to))
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
    parser.add_argument('--convert_to', '-c', type=str, 
                        help='Format for the converted DICOM file. Possible values are: "nrrd", '
                        '"nifti" and "nifti_gz". Default is nrrd.', default='nrrd')

    args = parser.parse_args()
  
    run_preparation(args.root, args.output, convert_to=args.convert_to)

print('Done!')
