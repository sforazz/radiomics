import os.path as op
import os
import shutil
import glob
import pydicom
from mhlib import Folder


def split_filename(fname):
    """Split a filename into parts: path, base filename and extension.
    Parameters
    ----------
    fname : str
        file or path name
    Returns
    -------
    pth : str
        base path from fname
    fname : str
        filename from fname, without extension
    ext : str
        file extension from fname
    """

    special_extensions = [".nii.gz", ".tar.gz", ".niml.dset"]

    pth = op.dirname(fname)
    fname = op.basename(fname)

    ext = None
    for special_ext in special_extensions:
        ext_len = len(special_ext)
        if (len(fname) > ext_len) and \
                (fname[-ext_len:].lower() == special_ext.lower()):
            ext = fname[-ext_len:]
            fname = fname[:-ext_len]
            break
    if not ext:
        fname, ext = op.splitext(fname)

    return pth, fname, ext


def mouse_ct_data_preparation(ct_folder):
    
    dicoms = sorted(glob.glob(ct_folder+'/*.IMA'))
    if not dicoms:
        dicoms = sorted(glob.glob(ct_folder+'/*.dcm'))
        if not dicoms:
            raise Exception('No DICOM files found in {}! Please check.'.format(ct_folder))
        else:
            ext = '.dcm'
    else:
        ext = '.IMA'
    
    sequence_numbers = list(set([x.split('.')[-11] for x in dicoms]))
    data_folders = []  # I will use this to store the sequence number of the CT data to convert
    for n_seq in sequence_numbers:                     
        dicom_vols = [x for x in dicoms if n_seq in x.split('.')[-11]]
        dcm_hd = pydicom.read_file(dicom_vols[0])
        if len(dicom_vols) > 1 and '50s' in dcm_hd.SeriesDescription:
            folder_name = ct_folder+'/Sequence_{}'.format(n_seq)
            if not os.path.isdir(folder_name):
                os.mkdir(folder_name)
                for x in dicom_vols:
                    shutil.copy2(x, folder_name)
            data_folders.append(folder_name)
    if not data_folders:
        raise Exception('No CT data with name containing "H50s" were found in {}'
                        .format(ct_folder))
    elif len(data_folders) > 1:
        print ('{0} datasets with name containing "H50s" were found in {1}. By default,'
               ' only the first one ({2}) will be used. Please check if this is correct.'
               .format(len(data_folders), ct_folder, data_folders[0]))

    return sorted(glob.glob(data_folders[0]+'/*{}'.format(ext)))[0]
