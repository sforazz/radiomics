#!/usr/bin/env python3.6
from converters.dicom import DicomConverters
from utils.filemanip import mouse_lung_data_preparation, batch_processing
import os
import argparse
from utils.image_preproc import cropping
import shutil


def mouse_fibrosis_data_preparation(input_data, root_path, work_dir, crop=False, clean=False):

    raw_data, mask_paths = batch_processing(input_data, root=root_path)
    
    for i, raw_data_folder in enumerate(raw_data):
        filename, folder_name = mouse_lung_data_preparation(raw_data_folder, work_dir)
        
        converter = DicomConverters(filename, clean=clean)
        converted_data = converter.mitk_converter()

        for j, mask in enumerate(os.listdir(mask_paths[i])):
            new_folder = folder_name+'/mouse_{}'.format(str(j+1).zfill(2))
            os.mkdir(new_folder)
            prefix = 'Raw_data_for_{}'.format(mask.split('.')[0])
            if crop:
                image, mask = cropping(converted_data, os.path.join(mask_paths[i], mask), prefix=prefix)
                shutil.move(image, new_folder)
                shutil.move(mask, new_folder)
            else:
                shutil.copy2(os.path.join(mask_paths[i], mask), new_folder)
                shutil.copy2(converted_data, os.path.join(new_folder, prefix))
        os.remove(converted_data)


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    
    parser.add_argument('input_file', type=str,
                        help=('Existing excel file with the paths to the raw data and'
                              ' the corresponding segmentation masks.'))
    parser.add_argument('work_dir', type=str,
                        help=('Path to the directory that will be created to store the results.'))
    parser.add_argument('--root', '-r', type=str, default='',
                        help=('Path to be appended to each file in the input_file. By default is empty.'))
    parser.add_argument('--crop', '-c', action='store_true', default=False,
                        help=('If provided, the images and the masks will be cropped to save '
                              'computational time.'))
    parser.add_argument('--clean', '-cl', action='store_true', default=False,
                        help=('If provided, the copied DICOM files in the working directory will be '
                              'deleted, leaving only the NRRD images (original size or cropped).'))
    
    args = parser.parse_args()
    
    mouse_fibrosis_data_preparation(args.input_file, args.root, args.work_dir, args.crop, args.clean)

    print('Done!')
