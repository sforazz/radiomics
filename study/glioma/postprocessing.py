import os
import glob
import csv
import pydicom
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
import collections
from core.utils.filemanip import mergedict
import shutil


EXTENSIONS = ['.nii.gz', '.csv']

tp_dict = {}
tp_dict['CT'] = 0
tp_dict['T1'] = 1
tp_dict['T1KM'] = 2
tp_dict['T2'] = 3
tp_dict['FLAIR'] = 4
tp_dict['ADC'] = 5
tp_dict['SWI'] = 6


def results_sorting(results_dir, raw_data_dir, outdir):

    subs = [x for x in os.listdir(results_dir) if os.path.isdir(os.path.join(results_dir, x))]
    results = collections.defaultdict(dict)
    
    for k in tp_dict.keys():
        outfile = os.path.join(outdir, 'result_features_extraction_{}.csv'.format(k))
        res = []
        no_res = 0
        for s in subs:
            results[s] = {}
            raw_data_path = os.path.join(raw_data_dir, s, "CT", "dcm")
            try:
                results_file = [x for x in sorted(glob.glob(os.path.join(results_dir, s)+'/*.csv'))
                                if os.stat(x).st_size != 0 and k in x.split('/')[-1].split('.')[0].split('_')
                                and 'Features' in x.split('/')[-1]][0]
                with open(results_file, 'r') as f:
                    data = csv.reader(f, delimiter=';')
                    res = [x for x in data]
                for i in range(5, len(res[0])):
                    results[s][res[0][i]] = res[1][i]
            except (IndexError, TypeError) as e:
                no_res += 1
                print('There is no csv file in {0} with name containing {1}'.format(os.path.join(results_dir, s), k))
        
            try:
                ref_dcm = sorted(glob.glob(raw_data_path+'/*.dcm'))[0]
                hd = pydicom.read_file(ref_dcm)
                try:
                    age = hd.PatientAge
                    age = int(age.strip('Y'))
                    results[s]['Age'] = age
                except AttributeError:
                    try:
                        bd = hd.PatientBirthDate
                        bd = dt.strptime(bd, '%Y%m%d')
                        ad = hd.AcquisitionDate
                        ad = dt.strptime(ad, '%Y%m%d')
                        age = relativedelta(ad, bd).years
                        results[s]['Age'] = age
                    except AttributeError:
                        print('{} does not have any age related attribute in the DICOM header.'.format(ref_dcm))
                try:
                    sex = hd.PatientSex
                    results[s]['Gender'] = sex
                except AttributeError:
                    print('{} does not have any gender related attribute in the DICOM header.'.format(ref_dcm))
            except IndexError:
                print('{} does not contain DICOM files! Patient info cannot be extracted'.format(raw_data_path))
        if no_res != 0:
            print('No results for features extracted from {0} for {1} subjects.'.format(k, no_res))
        try:
            fields = ['Patient', 'Age', 'Gender']+res[0][5:]
            with open(outfile, 'w') as csv_file:
                w = csv.DictWriter(csv_file, fields)
                w.writeheader()
                for k, d in sorted(results.items()):
                    w.writerow(mergedict({'Patient': k}, d))
        except IndexError:
            print('No subject with features extracted from {}'.format(k))
            pass


def renaming(result_dir, tp_dict):

    tp_dict_inv = {v: k for k, v in tp_dict.items()}
    data = [os.path.join(root, name) for root, _, files in os.walk(result_dir)
            for name in files if name.endswith('.csv')]
    if data:
        ext = 'csv'
    else:
        data = [os.path.join(root, name) for root, _, files in os.walk(result_dir)
                for name in files if name.endswith('.nii.gz')]
        if data:
            ext = 'nifti'
        else:
            raise Exception('No results found in {}'.format(result_dir))
    
    for d in data:
        if ext == 'csv':
            try:
                tp = int(d.split('/')[-1].split('_')[6])
            except ValueError:
                tp = int(d.split('/')[-1].split('_')[5])
            new_name = 'Features_extraction_from_{}.csv'.format(tp_dict_inv[tp])
        elif ext == 'nifti':
            tp = int(d.split('/')[-1].split('_')[1].split('#')[-1])
            new_name = '{}_registered_to_Reference.nii.gz'.format(tp_dict_inv[tp])
        d_path, _ = os.path.split(d)
        shutil.copy2(d, os.path.join(d_path, new_name))


raw_data_dir = '/mnt/sdb/Data_unsortiertO'
result_dir = '/mnt/sdb/CLEO_sorted_dc_session/CT_feature_ext/result'
outdir = '/home/fsforazz/Desktop/'

# renaming(result_dir, tp_dict)
results_sorting(result_dir, raw_data_dir, outdir)

print('Done!')
