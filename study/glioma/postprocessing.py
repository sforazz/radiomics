import os
import glob
import csv
import pydicom
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
import collections
from core.utils.filemanip import mergedict


raw_data_dir = '/media/fsforazz/extra_HD/Data_unsortiertO'
results_dir = '/media/fsforazz/extra_HD/glioma_dc_session/feature_ext_CT/result'
outfile = '/home/fsforazz/Desktop/results_feat_CT.csv'

subs = [x for x in os.listdir(results_dir) if os.path.isdir(os.path.join(results_dir, x))]
results = collections.defaultdict(dict)

for s in subs:
    results[s] = {}
    raw_data_path = os.path.join(raw_data_dir, s, "CT", "dcm")
    try:
        results_file = [x for x in sorted(glob.glob(os.path.join(results_dir, s)+'/*.csv')) if os.stat(x).st_size != 0][0]
        with open(results_file, 'r') as f:
            data = csv.reader(f, delimiter=';')
            res = [x for x in data]
        for i in range(5, len(res[0])):
            results[s][res[0][i]] = res[1][i]
    except IndexError:
        print('There is no not-empty csv file in {}'.format(os.path.join(results_dir, s)))

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

fields = ['Patient', 'Age', 'Gender']+res[0][5:]
with open(outfile, 'w') as csv_file:
    w = csv.DictWriter(csv_file, fields)
    w.writeheader()
    for k, d in sorted(results.items()):
        w.writerow(mergedict({'Patient': k}, d))

print('Done!')
