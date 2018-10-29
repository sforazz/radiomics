import subprocess as sp


class FeaturesCalc():
    
    def __init__(self, ct_data, mask):
        print ('Starting features extraction using {0} as CT data and {1} as mask...'
               .format(ct_data.split('/')[-1], mask.split('/')[-1]))
        self.ct_data = ct_data
        self.mask = mask
    
    
    def mitk(self):

        cmd = ('MitkCLGlobalImageFeatures -i "{0}" -m "{1}" -o MITK_features_calculation.csv -header -fo'
               .format(self.ct_data, self.mask))
        sp.check_output(cmd, shell=True)