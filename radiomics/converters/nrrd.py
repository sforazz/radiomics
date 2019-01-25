import nrrd
import nibabel as nib
import numpy as np
from radiomics.utils.filemanip import split_filename
import os


class NrrdConverters():
    
    def __init__(self, nrrd_file, ext='.nii.gz', outname=None):
        
        self.nrrd_file = nrrd_file
        path, filename, _ = split_filename(nrrd_file)
        if outname is None:
            self.outname = os.path.join(path, filename)+ext
        else:
            self.outname = outname+ext
    
    def nrrd2nifti(self):
        
        data, _ = nrrd.read(self.nrrd_file)
        tosave = nib.Nifti1Image(data, np.eye(4))
        nib.save(tosave, self.outname)