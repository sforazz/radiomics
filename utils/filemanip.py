import os.path as op
import os
import shutil
import glob
import pydicom
import pandas as pd


ALLOWED_EXT = ['.xlsx', '.csv']


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


def mouse_lung_data_preparation(raw_data):
    """Function to arrange the mouse lung data into a proper struture.
    In particular, this function will look into each raw_data folder searching for
    the data with H50s in the series description field in the DICOM header. Then,
    it will copy those data into another folder and will return the path to the first
    DICOM file that will be used to run the DICOM to NRRD conversion.
    Parameters
    ----------
    raw_data : str
        path to the raw data folder 
    Returns
    -------
    pth : str
        path to the first DICOM volume
    """
    
    dicoms = sorted(glob.glob(raw_data+'/*.IMA'))
    if not dicoms:
        dicoms = sorted(glob.glob(raw_data+'/*.dcm'))
        if not dicoms:
            raise Exception('No DICOM files found in {}! Please check.'.format(raw_data))
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
            folder_name = raw_data+'/Sequence_{}'.format(n_seq)
            if not os.path.isdir(folder_name):
                os.mkdir(folder_name)
                for x in dicom_vols:
                    shutil.copy2(x, folder_name)
            data_folders.append(folder_name)
    if not data_folders:
        raise Exception('No CT data with name containing "H50s" were found in {}'
                        .format(raw_data))
    elif len(data_folders) > 1:
        print ('{0} datasets with name containing "H50s" were found in {1}. By default,'
               ' only the first one ({2}) will be used. Please check if this is correct.'
               .format(len(data_folders), raw_data, data_folders[0]))

    return sorted(glob.glob(data_folders[0]+'/*{}'.format(ext)))[0]


def batch_processing(input_data, root=''):
    """Function to process the data in batch mode. It will take a .csv or .xlsx file with
    two columns. The first one called 'subjects' contains all the paths to the raw_data folders
    (one path per raw); the second one called 'masks' contains all the corresponding paths to 
    the segmented mask folders. 
    Parameters
    ----------
    input_data : str
        Excel or CSV file
    root : str
        (optional) root path to pre-pend to each subject and mask in the input_data file
    Returns
    -------
    raw_data : list
        list with all the subjects to process
    masks : list
        list with the corresponding mask to use to extract the features
    """
    if os.path.isfile(input_data):
        _, _, ext = split_filename(input_data)
        if ext not in ALLOWED_EXT:
            raise Exception('The file extension of the specified input file ({}) is not supported.'
                            ' The allowed extensions are: .xlsx or .csv')
        if ext == '.xlsx':
            files = pd.read_excel(input_data)
        elif ext == '.csv':
            files = pd.read_csv(input_data)
        files=files.dropna()
        masks = [os.path.join(root, str(x)) for x in list(files['masks'])]
        raw_data = [os.path.join(root, str(x)) for x in list(files['subjects'])] 

        return raw_data, masks
        