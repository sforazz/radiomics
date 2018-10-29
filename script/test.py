from converters.dicom import DicomConverters
from utils.filemanip import mouse_ct_data_preparation
import os
from features.features_calculation import FeaturesCalc


ct_folder = '/home/fsforazz/Desktop/PhD_project/fibrosis_project/Tr6_19w_CT/Tr6_20W_1/TR6_20WK_RT2_RT alone/TR6_20WK_RT2_RADIATION_ALONE'
masks_path = '/home/fsforazz/Desktop/PhD_project/fibrosis_project/analyzed data/RT/RT_2/'
filename = mouse_ct_data_preparation(ct_folder)

converter = DicomConverters(filename)
converted_ct = converter.slicer_converter()

for mask in os.listdir(masks_path):
    features = FeaturesCalc(converted_ct, os.path.join(masks_path, mask))
    features.mitk()

print 'Done!'