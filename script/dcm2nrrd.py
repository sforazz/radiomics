import glob
from utils.filemanip import dcm_info, dcm_check
import os
import shutil
from converters.dicom import DicomConverters


IMAGE_TO_PROCESS = ['BPLCT', 'PlanningMRI', 'FUMRI', 'FU_MRI']

root = '/home/fsforazz/Desktop/PhD_project/test_data_10-10-18/'
tempDir = '/home/fsforazz/Desktop/test_dcm2nrrd'
subjects = sorted(glob.glob(root+'/*'))

for sub in subjects:
    subName = sub.split('/')[-1]
    scans = [x for x in glob.glob(sub+'/*') if x.split('/')[-1]
             in IMAGE_TO_PROCESS]
    for scan in scans:
        scanName = scan.split('/')[-1]
        if scanName == 'FU_MRI':
            scanName = 'FUMRI'
        dirName = os.path.join(tempDir, subName, scanName)
        os.makedirs(dirName)

        dicoms, im_types, series_nums = dcm_info(scan)
        dicoms = dcm_check(dicoms, im_types, series_nums)

        for f in dicoms:
            shutil.copy2(f, dirName)
        
        converter = DicomConverters(dirName)
        converted_data = converter.mitk_converter()
        
print 'Done!'