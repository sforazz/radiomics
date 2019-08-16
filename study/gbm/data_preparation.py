from core.utils.dicom import dcm_info, dcm_check
import os
import shutil
from core.converters.dicom import DicomConverter
import argparse
from pathlib import Path
import nibabel as nib


IMAGE_TO_CHECK = ['CT', 'RTSTRUCT', 'T1', 'T1KM', 'T2', 'ADC', 'SWI', 'FLAIR', 'T2KM']
# to_process = ['0001508950', '0000308714', '0002189676', '0002325630']

def run_preparation(root, tempDir, convert_to='nrrd', ms=True):

    root = Path(root)
    tempDir = Path(tempDir)
#     subjects = sorted([root/x for x in root.iterdir() if x.is_dir() and x.parts[-1] in to_process])
    subjects = sorted([root/x for x in root.iterdir() if x.is_dir()])
    
    for sub in subjects:
        subName = sub.parts[-1]
        if not os.path.isdir(tempDir / subName):
            print('\nProcessing subject {}'.format(sub))
            if ms:
                sessions = sorted([sub/x for x in sub.iterdir() if x.is_dir()])
            else:
                sessions = [sub]
            for session in sessions:
                scans = {}
                sessionName = session.parts[-1]
                for im_t in IMAGE_TO_CHECK: 
                    scans[im_t] = [x for x in session.rglob('*.dcm') if x.parts[-3]==im_t and x.parts[-2].split('-')[0]=='1']
#                 for k in scans.keys(): 
#                     if not scans[k] and k == 'RTSTRUCT': 
#                         scans[k] = [x for x in session.rglob('*.dcm') if x.parts[-3]==k] 
#                     elif not scans[k] and not k == 'RTSTRUCT': 
#                         scans[k] = [x for x in session.rglob('*.dcm') if x.parts[-5]==k and x.parts[-3].split('_')[0]=='1']
                
#                 for k in scans.keys():
#                     if scans[k] and not k == 'RTSTRUCT':
#                         series = sorted(list(set([x.parts[-3] for x in scans[k]])))
#                         if len(series) > 1:
#                             imgs = [x for x in scans[k] if x.parts[-3]==series[0]]
#                             scans[k] = imgs
        
                for scan in scans.keys():
                    images = scans[scan]
                    if images:
#                         if scan == 'RTSTRUCT':
#                             scanName = images[0].parts[-3]
#                         else:
                        scanName = images[0].parts[-3]
                        if ms:
                            dirName = tempDir / subName / sessionName / scanName
                        else:
                            dirName = tempDir / subName / scanName
                        if not os.path.isdir(dirName):
                            os.makedirs(dirName)
                        else:
                            shutil.rmtree(dirName)
                            os.makedirs(dirName)
                        
                        if scan != 'RTSTRUCT':
                            dicoms, im_types, series_nums = dcm_info(images)
                            dicoms = dcm_check(dicoms, im_types, series_nums)
                            for f in dicoms:
                                shutil.copy2(f, dirName)
                            if dicoms:
                                converter = DicomConverter(str(dirName))
                                converter.convert(convert_to=convert_to)
#                                 extra = [x for x in sorted(list(dirName.parent.glob('*.nii.gz'))) if str(x) != str(dirName.parent)+'/{}.nii.gz'.format(scanName)]
                                extra = sorted(list(dirName.parent.glob('{}_*.nii.gz'.format(scanName))))
                                converted = sorted(list(dirName.parent.glob('{}.nii.gz'.format(scanName))))
                                to_remove = []
                                if len(extra) == 2 and scanName == 'T2':
                                    to_remove.append(extra[0])
                                    os.rename(extra[1], str(extra[1].parent)+'/T2.nii.gz')
                                    converted = sorted(list(dirName.parent.glob('{}.nii.gz'.format(scanName))))
                                elif len(extra) == 1:
                                    to_remove = to_remove+extra
                                elif len(extra) > 1 and scanName == 'CT':
                                    to_remove = to_remove+extra
                                    converter = DicomConverter(str(dirName))
                                    converter.convert(convert_to=convert_to, force=True)
                                    converted = sorted(list(dirName.parent.glob('{}.nii.gz'.format(scanName))))
                                    extra = [x for x in sorted(list(dirName.parent.glob('{}_*.nii.gz'.format(scanName)))) if x not in to_remove]
                                if len(extra) == 1 and [x for x in extra if 'CT_Tilt' in str(x)]:
                                    try:
                                        os.remove(str(extra[0].parent)+'/CT.nii.gz')
                                    except:
                                        pass
                                    os.rename(extra[0], str(extra[0].parent)+'/CT.nii.gz')
                                    try:
                                        to_remove.remove(extra[0])
                                    except ValueError:
                                        pass
                                if len(converted) == 0:
                                    print('No converted file for {}. Something went wrong!Check!'.format(scanName))
                                if to_remove:
                                    for f in to_remove:
                                        os.remove(f)
                                if scanName != 'CT':
                                    shutil.rmtree(dirName)
                            else:
                                print('{} folder seems to do not contain any correct DICOM files.'
                                      ' Conversion cannot be made and it will be ignored.'.format(scan))
                        else:
                            for f in images:
                                shutil.copy2(f, dirName)
        else:
            print('Subject already processed. Skipping')

    converted_files = [os.path.join(root, name) for root, _, files in os.walk(tempDir)
            for name in files if name.endswith('.nii.gz')]
    print(len(converted_files))
    to_remove = []
    for f in converted_files:
        try:
            ref = nib.load(f)
            data = ref.get_data()
            if len(data.squeeze().shape) == 2 or len(data.squeeze().shape) > 4:
                to_remove.append(f)
            elif len(data.squeeze().shape) == 4:
                im2save = nib.Nifti1Image(data[:, :, :, 0], affine=ref.affine)
                nib.save(im2save, f)
            elif len(data.dtype) > 0:
                print('{} is not a greyscale image. It will be deleted.'.format(f))
                to_remove.append(f)
        except:
            print('{} failed to save with nibabel. It will be deleted.'.format(f))
            to_remove.append(f)
    print(len(to_remove))
    if to_remove:
        for f in to_remove:
            os.remove(f)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--root', '-r', type=str)
    parser.add_argument('--output', '-o', type=str)
    parser.add_argument('--convert_to', '-c', type=str, 
                        help='Format for the converted DICOM file. Possible values are: "nrrd", '
                        '"nifti" and "nifti_gz". Default is nrrd.', default='nrrd')
    parser.add_argument('--multiSession', '-ms', default=False, action='store_true',
                        help='Whether or not the subjects were acquired multiple times.')

    args = parser.parse_args()
  
    run_preparation(args.root, args.output, convert_to=args.convert_to, ms=args.multiSession)

print('Done!')
