import os, glob
import numpy as np
import pydicom
from skimage.draw import polygon
import subprocess as sp
import nibabel
from pydicom.tag import Tag
from skimage import draw


class DicomImagestoData:
    def __init__(self,path=''):
        self.associations = {}
        self.hierarchy = {}
        self.down_folder(path)

    def down_folder(self,input_path):
        files = []
        dirs = []
        file = []
        for root, dirs, files in os.walk(input_path):
            break
        for val in files:
            if val.find('.dcm') != -1:
                file = val
                break
        if file and input_path:
            self.Make_Contour_From_directory(input_path)
        for dir in dirs:
            new_directory = os.path.join(input_path,dir)
            self.down_folder(new_directory)
        return None

    def get_mask(self, Contour_Names):
        for roi in Contour_Names:
            if roi not in self.associations:
                self.associations[roi] = roi
        self.Contour_Names = Contour_Names

        # And this is making a mask file
        self.mask = np.zeros([self.image_size_1, self.image_size_2, len(self.lstFilesDCM), len(self.Contour_Names)],
                             dtype='float32')

        self.structure_references = {}
        for contour_number in range(len(self.RS_struct.ROIContourSequence)):
            self.structure_references[
                self.RS_struct.ROIContourSequence[contour_number].ReferencedROINumber] = contour_number

        found_rois = {}
        for roi in self.Contour_Names:
            found_rois[roi] = {'Hierarchy': 999, 'Name': [], 'Roi_Number': 0}
        for Structures in self.ROI_Structure:
            ROI_Name = Structures.ROIName
            if Structures.ROINumber not in self.structure_references.keys():
                continue
            true_name = None
            if ROI_Name in self.associations:
                true_name = self.associations[ROI_Name]
            elif ROI_Name in self.associations:
                true_name = self.associations[ROI_Name]
            if true_name and true_name in self.Contour_Names:
                if true_name in self.hierarchy.keys():
                    for roi in self.hierarchy[true_name]:
                        if roi == ROI_Name:
                            index_val = self.hierarchy[true_name].index(roi)
                            if index_val < found_rois[true_name]['Hierarchy']:
                                found_rois[true_name]['Hierarchy'] = index_val
                                found_rois[true_name]['Name'] = ROI_Name
                                found_rois[true_name]['Roi_Number'] = Structures.ROINumber
                else:
                    found_rois[true_name] = {'Hierarchy': 999, 'Name': ROI_Name, 'Roi_Number': Structures.ROINumber}
        i = 0
        for ROI_Name in found_rois.keys():
            if found_rois[ROI_Name]['Roi_Number'] in self.structure_references:
                index = self.structure_references[found_rois[ROI_Name]['Roi_Number']]
                mask = self.get_mask_for_contour(index)
                self.mask[..., i][mask == 1] = 1
                i += 1
        self.mask = np.transpose(self.mask, axes=(2, 0, 1, 3))
        return None

    def Make_Contour_From_directory(self,PathDicom):
        self.prep_data(PathDicom)
        self.all_angles = [0]
        self.get_images_and_mask()
        return None
    def prep_data(self,PathDicom):
        self.PathDicom = PathDicom
        self.lstFilesDCM = []
        self.lstRSFile = []
        self.Dicom_info = []

        fileList = []
        for dirName, dirs, fileList in os.walk(PathDicom):
            break
        if len(fileList) < 10: # If there are no files, break out
            return None
        for filename in fileList:
            try:
                ds = pydicom.read_file(os.path.join(dirName,filename))
                if ds.Modality == 'CT' or ds.Modality == 'MR':  # check whether the file's DICOM
                    self.lstFilesDCM.append(os.path.join(dirName, filename))
                    self.Dicom_info.append(ds)
                elif ds.Modality == 'RTSTRUCT':
                    self.lstRSFile = os.path.join(dirName, filename)
            except:
                # if filename.find('Iteration_') == 0:
                #     os.remove(PathDicom+filename)
                continue
        self.RefDs = pydicom.read_file(self.lstFilesDCM[0])
        self.mask_exist = False
        if self.lstRSFile:
            self.RS_struct = pydicom.read_file(self.lstRSFile)
            if Tag((0x3006,0x020)) in self.RS_struct.keys():
                self.ROI_Structure = self.RS_struct.StructureSetROISequence
            else:
                self.ROI_Structure = []
            self.rois_in_case = []
            for Structures in self.ROI_Structure:
                self.rois_in_case.append(Structures.ROIName)

    def get_images_and_mask(self):
        # Working on the RS structure now
        # The array is sized based on 'ConstPixelDims'
        # ArrayDicom = np.zeros(ConstPixelDims, dtype=RefDs.pixel_array.dtype)
        if self.lstRSFile:
            checking_mult = pydicom.read_file(self.lstRSFile)
            checking_mult = round(checking_mult.ROIContourSequence[0].ContourSequence[0].ContourData[2],2)
        self.image_size_1 = self.Dicom_info[0].pixel_array.shape[0]
        self.image_size_2 = self.Dicom_info[0].pixel_array.shape[1]
        self.ArrayDicom = np.zeros([self.image_size_1, self.image_size_2, len(self.lstFilesDCM)], dtype='float32')

        # loop through all the DICOM files
        self.slice_locations = []
        self.slice_info = np.zeros([len(self.lstFilesDCM)])
        self.SOPClassUID_temp = {}
        self.mult = 1
        # This makes the dicom array of 'real' images
        for filenameDCM in self.lstFilesDCM:
            # read the file
            self.ds = self.Dicom_info[self.lstFilesDCM.index(filenameDCM)]
            # store the raw image data
            if self.ds.pixel_array.shape[0] != self.image_size_1:
                print('Size issue')
            else:
                im = self.ds.pixel_array
            # im[im<200] = 200 #Don't know what the hell these units are, but the min (air) is 0
            self.ArrayDicom[:, :, self.lstFilesDCM.index(filenameDCM)] = im
            # Get slice locations
            slice_location = round(self.ds.ImagePositionPatient[2],2)
            self.slice_locations.append(slice_location)
            self.slice_info[self.lstFilesDCM.index(filenameDCM)] = round(self.ds.ImagePositionPatient[2],3)
            self.SOPClassUID_temp[self.lstFilesDCM.index(filenameDCM)] = self.ds.SOPInstanceUID
        try:
            RescaleIntercept = self.ds.RescaleIntercept
            RescaleSlope = self.ds.RescaleSlope
        except:
            RescaleIntercept = 1
            RescaleSlope = 1
        if self.lstRSFile:
            if min([abs(i - checking_mult) for i in self.slice_locations]) < 0.01:
                self.mult = 1
            elif min([abs(i - checking_mult) for i in self.slice_locations]) < 0.01:
                self.mult = -1
            else:
                print('Slice values are off..')
                self.skip_val = True
                return None
        self.ArrayDicom = (self.ArrayDicom+RescaleIntercept)/RescaleSlope
        indexes = [i[0] for i in sorted(enumerate(self.slice_locations), key=lambda x: x[1])]
        self.ArrayDicom = self.ArrayDicom[:, :, indexes]
        self.ArrayDicom = np.transpose(self.ArrayDicom,[-1,0,1])
        self.slice_info = self.slice_info[indexes]
        self.SeriesInstanceUID = self.ds.SeriesInstanceUID
        self.slice_locations.sort()
        self.SOPClassUID = {}
        i = 0
        for index in indexes:
            self.SOPClassUID[i] = self.SOPClassUID_temp[index]
            i += 1

    def get_mask_for_contour(self,i):
        self.Liver_Locations = self.RS_struct.ROIContourSequence[i].ContourSequence
        self.Liver_Slices = []
        for contours in self.Liver_Locations:
            data_point = contours.ContourData[2]
            if data_point not in self.Liver_Slices:
                self.Liver_Slices.append(contours.ContourData[2])
        return self.Contours_to_mask()

    def Contours_to_mask(self):
        mask = np.zeros([self.image_size_1, self.image_size_2, len(self.lstFilesDCM)], dtype='float32')
        Contour_data = self.Liver_Locations
        ShiftCols = self.RefDs.ImagePositionPatient[0]
        ShiftRows = self.RefDs.ImagePositionPatient[1]
        PixelSize = self.RefDs.PixelSpacing[0]
        Mag = 1 / PixelSize
        mult1 = mult2 = 1
        if ShiftCols > 0:
            mult1 = -1
        if ShiftRows > 0:
            print('take a look at this one...')
        #    mult2 = -1

        for i in range(len(Contour_data)):
            slice_val = round(Contour_data[i].ContourData[2],2)
            dif = [abs(i * self.mult - slice_val) for i in self.slice_locations]
            try:
                slice_index = dif.index(min(dif))  # Now we know which slice to alter in the mask file
            except:
                print('might have had an issue here..')
                continue
            cols = Contour_data[i].ContourData[1::3]
            rows = Contour_data[i].ContourData[0::3]
            self.col_val = [Mag * abs(x - mult1 * ShiftRows) for x in cols]
            self.row_val = [Mag * abs(x - mult2 * ShiftCols) for x in rows]
            temp_mask = self.poly2mask(self.col_val, self.row_val, [self.image_size_1, self.image_size_2])
            mask[:,:,slice_index][temp_mask > 0] = 1
            #scm.imsave('C:\\Users\\bmanderson\\desktop\\images\\mask_'+str(i)+'.png',mask_slice)

        return mask

    def poly2mask(self,vertex_row_coords, vertex_col_coords, shape):
        fill_row_coords, fill_col_coords = draw.polygon(vertex_row_coords, vertex_col_coords, shape)
        mask = np.zeros(shape, dtype=np.bool)
        mask[fill_row_coords, fill_col_coords] = True
        return mask


def read_structure(structure):
    contours = []
    for i in range(len(structure.ROIContourSequence)):
        contour = {}
        contour['color'] = structure.ROIContourSequence[i].ROIDisplayColor
        contour['number'] = structure.ROIContourSequence[i].ReferencedROINumber
        contour['name'] = structure.StructureSetROISequence[i].ROIName
        if contour['number'] == structure.StructureSetROISequence[i].ROINumber:
            print('Assertion failed for contour: {}'.format(contour['name']))
#         assert contour['number'] == structure.StructureSetROISequence[i].ROINumber
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


def contour_names(structure):

    names = []
    for i in range(len(structure.ROIContourSequence)):
        names.append(structure.StructureSetROISequence[i].ROIName)
    return names


def export_RTS(patient, contours2extract=['GTV', 'CTV', 'PTV'], force_no_flip=False):

    reference = os.path.join(patient, 'CT.nii.gz')
    if force_no_flip:
        ct = os.path.join(patient, "CT")
        cmd = 'dcm2niix -o {0} -z y -f CT_no_flip {1}'.format(patient, ct)
        sp.check_output(cmd, shell=True)
        reference = os.path.join(patient, 'CT_no_flip.nii.gz')
#     _, ref_hd = nrrd.read(reference)
    ref_hd = nibabel.load(reference)
    dcms = glob.glob(os.path.join(patient, "CT", "*.dcm"))
    structCT = glob.glob(os.path.join(patient, "RTSTRUCT/*.dcm"))[0]
    
    structure = pydicom.read_file(structCT)
    try:
        contours = read_structure(structure)
        slices = [pydicom.read_file(dcm) for dcm in dcms]
        slices.sort(key = lambda x: float(x.ImagePositionPatient[2]))
        image = np.stack([s.pixel_array for s in slices], axis=-1)
        processed = []
        for con in contours:
            if 'gtv' in con['name'].lower():
                print('Extracting {} from the RT Structure set...'.format(con['name']))
                label = get_mask(con, slices, image)
    #             nrrd.write(os.path.join(patient, con['name']+'.nrrd'), label, header=ref_hd)
                im2save = nibabel.Nifti1Image(label, affine=ref_hd.affine)
                nibabel.save(im2save, os.path.join(patient, con['name']+'.nii.gz'))
                processed.append(con['name'])
        if len(contours2extract) != len(processed):
            missing = [x for x in contours2extract if x not in processed]
        else:
            missing = []
    except:
        missing = []
        pass
    
    return missing
