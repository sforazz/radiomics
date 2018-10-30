from converters.dicom import DicomConverters
from utils.filemanip import mouse_lung_data_preparation, batch_processing
import os
from features.features_calculation import FeaturesCalc


input_data = '/home/fsforazz/Desktop/PhD_project/fibrosis_project/input_data.xlsx'
root_path = '/home/fsforazz/Desktop/PhD_project/fibrosis_project'

raw_data, mask_paths = batch_processing(input_data, root=root_path)

for i, raw_data_folder in enumerate(raw_data):
    filename = mouse_lung_data_preparation(raw_data_folder)
    
    converter = DicomConverters(filename)
    converted_data = converter.slicer_converter()
    
    for mask in os.listdir(mask_paths[i]):
        features = FeaturesCalc(converted_data, os.path.join(mask_paths[i], mask))
        features.mitk()

print 'Done!'