import subprocess as sp
from radiomics.utils.filemanip import split_filename, clean_folder
import os


class DicomConverters():

    def __init__(self, dicom, ext='.nrrd', clean=False):
        print ('\nStarting the DICOM conversion of {0}...'.format(dicom.split('/')[-1]))
        self.dicom_file = dicom
        if os.path.isdir(self.dicom_file):
            self.dicom_folder = self.dicom_file
        else:
            self.dicom_folder, _, _ = split_filename(self.dicom_file)
        self.path, self.filename, _ = split_filename(dicom)
#         self.outname = os.path.join(path, filename)+ext
        self.clean = clean
        self.ext = ext


    def slicer_converter(self):

        outname = os.path.join(self.path, self.filename)+self.ext
        cmd = (('Slicer --no-main-window --python-code '+'"node=slicer.util.loadVolume('+
                "'{0}', returnNode=True)[1]; slicer.util.saveNode(node, '{1}'); exit()"+'"')
                .format(self.dicom_file, outname))
        sp.check_output(cmd, shell=True)
        
        return outname

    def mitk_converter(self):
        
        outname = os.path.join(self.path, self.filename)+self.ext

        cmd = ("MitkCLDicom2Nrrd -i '{0}' -o '{1}'".format(self.dicom_folder, outname))
        sp.check_output(cmd, shell=True, stderr=sp.STDOUT)

        if self.clean:
            clean_folder(self.dicom_folder)

        print('Conversion done!\n')
        return outname

    def dcm2niix_converter(self, compress=True):

        outname = os.path.join(self.path, self.filename)+self.ext
        if compress:
            cmd = ("dcm2niix -o {0} -f {1} -z y {2}".format(self.path, self.filename,
                                                            self.dicom_folder))
        else:
            cmd = ("dcm2niix -o {0} -f {1} {2}".format(self.path, self.filename,
                                                       self.dicom_folder))
        sp.check_output(cmd, shell=True)

        if self.clean:
            clean_folder(self.dicom_folder)

        print('Conversion done!\n')
        return outname
