import os, glob
import numpy as np
import pydicom
from skimage.draw import polygon
import nrrd


def read_structure(structure):
    contours = []
    for i in range(len(structure.ROIContourSequence)):
        contour = {}
        contour['color'] = structure.ROIContourSequence[i].ROIDisplayColor
        contour['number'] = structure.ROIContourSequence[i].ReferencedROINumber
        contour['name'] = structure.StructureSetROISequence[i].ROIName
        assert contour['number'] == structure.StructureSetROISequence[i].ROINumber
        contour['contours'] = [s.ContourData for s in structure.ROIContourSequence[i].ContourSequence]
        contours.append(contour)
    return contours


def get_mask(con, slices, image):

    z = [s.ImagePositionPatient[2] for s in slices]
    pos_r = slices[0].ImagePositionPatient[1]
    spacing_r = slices[0].PixelSpacing[1]
    pos_c = slices[0].ImagePositionPatient[0]
    spacing_c = slices[0].PixelSpacing[0]
    
    label = np.zeros_like(image, dtype=np.uint8)
    for c in con['contours']:
        nodes = np.array(c).reshape((-1, 3))
        try:
            assert np.amax(np.abs(np.diff(nodes[:, 2]))) == 0
        except:
            print('assertion failed.')
        z_index = z.index(np.around(nodes[0, 2], 1))
        r = (nodes[:, 1] - pos_r) / spacing_r
        c = (nodes[:, 0] - pos_c) / spacing_c
        rr, cc = polygon(r, c)
        label[cc, rr, z_index] = 1
    
    return label


def export_RTS(patient, contours2extract=['GTV', 'CTV', 'PTV']):

    reference = os.path.join(patient, 'BPLCT.nrrd')
    _, ref_hd = nrrd.read(reference)
    dcms = glob.glob(os.path.join(patient, "BPLCT", "*.dcm"))
    structCT = glob.glob(os.path.join(patient, "RTPLAN", "RTSTRUCT_*.dcm"))[0]
    
    structure = pydicom.read_file(structCT)
    contours = read_structure(structure)
    slices = [pydicom.read_file(dcm) for dcm in dcms]
    slices.sort(key = lambda x: float(x.ImagePositionPatient[2]))
    image = np.stack([s.pixel_array for s in slices], axis=-1)
    processed = []
    for con in contours:
        if con['name'] in contours2extract:
            print('Extracting {} from the RT Structure set...'.format(con['name']))
            label = get_mask(con, slices, image)
            nrrd.write(os.path.join(patient, con['name']+'.nrrd'), label, header=ref_hd)
            processed.append(con['name'])
    if len(contours2extract) != len(processed):
        missing = [x for x in contours2extract if x not in processed]
    else:
        missing = []
    
    return missing
