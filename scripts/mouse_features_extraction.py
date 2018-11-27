from Radiomics.converters.dicom import DicomConverters
from Radiomics.utils.filemanip import mouse_lung_data_preparation, batch_processing
import os
from Radiomics.features.features_calculation import FeaturesCalc
import argparse


# input_data = '/home/fsforazz/Desktop/PhD_project/fibrosis_project/input_data.xlsx'
# root_path = '/home/fsforazz/Desktop/PhD_project/fibrosis_project'
# temp_dir = '/home/fsforazz/Desktop/mouse_fibrosis_feature_extraction_no_crop'

def run_features_extraction(input_data, root_path, work_dir, crop=False):

    raw_data, mask_paths = batch_processing(input_data, root=root_path)
    
    for i, raw_data_folder in enumerate(raw_data):
        filename = mouse_lung_data_preparation(raw_data_folder, work_dir)
        
        converter = DicomConverters(filename)
        converted_data = converter.mitk_converter()
        
        for mask in os.listdir(mask_paths[i]):
            features = FeaturesCalc(converted_data, os.path.join(mask_paths[i], mask), crop=crop)
            features.mitk()


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    
    parser.add_argument('--input_file', '-in', type=str,
                        help=('Existing excel file with the paths to the raw data and'
                              ' the corresponding segmentation masks.'))
    parser.add_argument('--root', 'r', type=str,
                        help=('Path to be appended to each file in the input_file.'))
    parser.add_argument('--work_dir', '-w', type=str,
                        help=('Path to the directory that will be created to store the results.'))
    parser.add_argument('--crop', '-c', action='store_true',
                        help=('If provided, the images and the masks will be cropped to save '
                              'computational time.'))
    
    args = parser.parse_args()
    
    run_features_extraction(args.input_file, args.root, args.work_dir, args.crop)

    print('Done!')