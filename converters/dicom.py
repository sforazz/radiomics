import subprocess as sp
from utils.filemanip import split_filename
import os
import glob


class DicomConverters():

    def __init__(self, dicom, ext='.nrrd', clean=False):
        print ('\nStarting conversion of {0} from DICOM to NRRD...'.format(dicom.split('/')[-1]))
        self.dicom_file = dicom
        path, filename, _ = split_filename(dicom)
        self.outname = os.path.join(path, filename)+ext
        self.clean = clean


    def slicer_converter(self):

        cmd = (('Slicer --no-main-window --python-code '+'"node=slicer.util.loadVolume('+
                "'{0}', returnNode=True)[1]; slicer.util.saveNode(node, '{1}'); exit()"+'"')
                .format(self.dicom_file, self.outname))
        sp.check_output(cmd, shell=True)
        
        return self.outname

    def mitk_converter(self):
        
        if os.path.isdir(self.dicom_file):
            dicom_folder = self.dicom_file
        else:
            dicom_folder, _, _ = split_filename(self.dicom_file)
        try:
            cmd = ("MitkCLDicom2Nrrd -i '{0}' -o '{1}'".format(dicom_folder, self.outname))
            sp.check_output(cmd, shell=True, stderr=sp.STDOUT)
        except sp.CalledProcessError as e:
            print ("command '{}' return with error (code {}): {}"
                   .format(e.cmd, e.returncode, e.output))
            print ("If the DICOM to NRRD conversion gave you the segmentation fault error, do not "
                   "panic. Usually it gives that error after the conversion so you should have "
                   "your converted data. I do not know why this happens yet.")
        if self.clean:
            toDelete = glob.glob(dicom_folder+'/*.IMA')
            if not toDelete:
                toDelete = glob.glob(dicom_folder+'/*.dcm')
            if toDelete:
                for f in toDelete:
                    os.remove(f)
        print('Conversion done!\n')
        return self.outname
