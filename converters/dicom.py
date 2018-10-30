import subprocess as sp
from utils.filemanip import split_filename
import os


class DicomConverters():

    def __init__(self, dicom, ext='.nrrd'):
        print ('\nStarting conversion of {0} from DICOM to NRRD...\n'.format(dicom.split('/')[-1]))
        self.dicom_file = dicom
        path, filename, _ = split_filename(dicom)
        self.outname = os.path.join(path, filename)+ext


    def slicer_converter(self):

        cmd = (('Slicer --no-main-window --python-code '+'"node=slicer.util.loadVolume('+
                "'{0}', returnNode=True)[1]; slicer.util.saveNode(node, '{1}'); exit()"+'"')
                .format(self.dicom_file, self.outname))
        sp.check_output(cmd, shell=True)
        
        return self.outname
