#!/usr/bin/env python3.6
from core.converters.dicom import DicomConverter
from core.utils.filemanip import batch_processing
import os
import argparse
from core.process.preprocess import mouse_lung_data_preparation
from core.converters.nrrd import NrrdConverter
from core.process.crop import ImageCropping


def mouse_fibrosis_data_preparation(input_data, root_path, work_dir, crop=False, clean=False,
                                    save_nii=True):

    raw_data, mask_paths = batch_processing(input_data, root=root_path)
    processed_subs = []
    if os.path.isfile(os.path.join(work_dir, 'processed_subjects.txt')):
        with open(os.path.join(work_dir, 'processed_subjects.txt'), 'r') as f:
            for line in f:
                processed_subs.append(line.strip())
    for i, raw_data_folder in enumerate(raw_data):
        if raw_data_folder not in processed_subs:
            print('Processing subject {}\n'.format(raw_data_folder.split('/')[-1]))
            filename, _, _ = mouse_lung_data_preparation(raw_data_folder, work_dir)
            if filename:
                converter = DicomConverter(filename, clean=clean)
                converted_data = converter.convert(convert_to='nrrd', method='mitk')
                
                if crop:
                    images = []
                    if mask_paths is not None:
                        for mask in os.listdir(mask_paths[i]):
                            if os.path.isfile(os.path.join(mask_paths[i], mask)):
                                prefix = 'Raw_data_for_{}'.format(mask.split('.')[0])
                                cropping = ImageCropping(converted_data, os.path.join(mask_paths[i], mask),
                                                         prefix=prefix)
                                image, mask = cropping.crop_with_mask()
                                if image is not None:
                                    images.append(image)
                                    images.append(mask)
                    else:
                        cropping = ImageCropping(converted_data)
                        cropped = cropping.crop_wo_mask()
                        images = images + cropped
                    if images:
                        for f in images:
                            if save_nii:
                                nrrd2nifti = NrrdConverter(f)
                                nrrd2nifti.convert()
            
                os.remove(converted_data)
                with open(os.path.join(work_dir, 'processed_subjects.txt'), 'a') as f:
                    f.write(raw_data_folder+'\n')
            else:
                with open(os.path.join(work_dir, 'skipped_subjects.txt'), 'a') as f:
                    f.write(raw_data_folder+'\n')
        else:
            print('{} has already been processed and will be skipped.'.format(raw_data_folder))


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
    parser.add_argument('--save_nii', '-sn', action='store_true', default=False,
                        help=('If provided, the cropped images and masks will be saved as nii.gz in '
                              'this folder.'))
    
    args = parser.parse_args()
    
    mouse_fibrosis_data_preparation(args.input_file, args.root, args.work_dir, args.crop, args.clean,
                                    args.save_nii)

    print('Done!')
