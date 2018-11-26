import os.path as op
import os
import shutil
import glob
import pydicom
import pandas as pd
import numpy as np
from operator import itemgetter


ALLOWED_EXT = ['.xlsx', '.csv']
ILLEGAL_CHARACTERS = ['/', '(', ')', '[', ']', '{', '}', ' ', '-']

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


def mouse_lung_data_preparation(raw_data, temp_dir):
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
    
    if not os.path.isdir(temp_dir):
        os.mkdir(temp_dir)
    basename = raw_data.split('/')[-1]
    sequence_numbers = list(set([x.split('.')[-11] for x in dicoms]))
    for character in ILLEGAL_CHARACTERS:
        basename = basename.replace(character, '_')
    data_folders = []  # I will use this to store the sequence number of the CT data to convert
    for n_seq in sequence_numbers:                     
        dicom_vols = [x for x in dicoms if n_seq in x.split('.')[-11]]
        dcm_hd = pydicom.read_file(dicom_vols[0])
        if len(dicom_vols) > 1 and '50s' in dcm_hd.SeriesDescription:
            folder_name = temp_dir+'/{0}_Sequence_{1}'.format(basename, n_seq)
            if not os.path.isdir(folder_name):
                os.mkdir(folder_name)
            else:
                shutil.rmtree(folder_name)
                os.mkdir(folder_name)
            for x in dicom_vols:
                try:
                    shutil.copy2(x, folder_name)
                except:
                    continue
            data_folders.append(folder_name)
    if not data_folders:
        raise Exception('No CT data with name containing "H50s" were found in {}'
                        .format(raw_data))
    elif len(data_folders) > 1:
        print ('{0} datasets with name containing "H50s" were found in {1}. By default,'
               ' only the first one ({2}) will be used. Please check if this is correct.'
               .format(len(data_folders), raw_data, data_folders[0]))

    return sorted(glob.glob(data_folders[0]+'/*{}'.format(ext)))[0], folder_name


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


def dcm_info(dcm_folder):
    """Function to extract information from a list of DICOM files in one folder. It returns a list of
    unique image types and scan numbers found in the input list of DICOMS.
    Parameters
    ----------
    dcm_folder : str
        path to an existing folder with DICOM files
    Returns
    -------
    dicoms : list
        list of DICOM files in the folder
    image_types : list
        list of unique image types extracted from the DICOMS
    series_nums : list
        list of unique series numbers extracted from the DICOMS
    """
    dicoms = sorted(glob.glob(dcm_folder+'/*.dcm'))
    if not dicoms:
        dicoms = sorted(glob.glob(dcm_folder+'/*.IMA'))
        if not dicoms:
            raise Exception('No DICOM files found in {}'.format(dcm_folder))
    ImageTypes = []
    SeriesNums = []
    AcqTimes = []
    toRemove = []
    for dcm in dicoms:
        header = pydicom.read_file(dcm)
        try:
            ImageTypes.append(tuple(header.ImageType))
            SeriesNums.append(header.SeriesNumber)
            AcqTimes.append(header.AcquisitionTime) 
        except AttributeError:
            print ('{} seems to do not have the right DICOM fields and '
                   'will be removed from the folder'.format(dcm))
            toRemove.append(dcm)
    if len(AcqTimes) == 2*(len(set(AcqTimes))):
        sortedAcqTm = sorted(zip(dicoms, AcqTimes), key=itemgetter(1))
        uniqueAcqTms = [x[0] for x in sortedAcqTm[:][0:-1:2]]
        toRemove = toRemove+uniqueAcqTms
    if toRemove:
        for f in toRemove:
            dicoms.remove(f)
    
    return dicoms, list(set(ImageTypes)), list(set(SeriesNums))


def dcm_check(dicoms, im_types, series_nums):
    """Function to check the DICOM files in one folder. It is based on the glioma test data.
    This function checks the type of the image (to exclude those that are localizer acquisitions)
    and the series number (if in one folder there are more than one scans then this function will
    return the second one, assuming that it is the one after the contrast agent injection).
    It returns a list of DICOMS which belong to one scan only, ignoring localizer scans. 
    Parameters
    ----------
    dicoms : list
        list of DICOMS in one folder
    im_types : list
        list of all image types extracted from the DICOM headers
    series_nums : list
        list of all scan numbers extracted from the DICOM headers
    Returns
    -------
    dcms : list
        list of DICOMS files
    """
    if len(im_types) > 1:
        im_type = list([x for x in im_types if not
                        'PROJECTION IMAGE' in x][0])

        dcms = [x for x in dicoms if pydicom.read_file(x).ImageType==im_type]
    elif len(series_nums) > 1:
        series_num = np.max(series_nums)
        dcms = [x for x in dicoms if pydicom.read_file(x).SeriesNumber==series_num]
    else:
        dcms = dicoms
    
    return dcms