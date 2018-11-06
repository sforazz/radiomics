import subprocess as sp
from utils.image_preproc import cropping


class FeaturesCalc():
    
    def __init__(self, raw_data, mask, crop=False):
        
        if crop:
            cropped_data, cropped_mask = cropping(raw_data, mask)
            self.raw_data = cropped_data
            self.mask = cropped_mask
        else:
            self.raw_data = raw_data
            self.mask = mask
        print ('\nStarting features extraction using {0} as raw data and {1} as mask...'
               .format(self.raw_data.split('/')[-1], self.mask.split('/')[-1]))
    
    def mitk(self):
    
        try:
            cmd = ('MitkCLGlobalImageFeatures -i "{0}" -m "{1}" -o MITK_features_calculation.csv '
                   '-header -fo -ivoh -loci -vol -volden -cooc2 -ngld -rl -id -ngtd'
                   .format(self.raw_data, self.mask))
            sp.check_output(cmd, shell=True, stderr=sp.STDOUT)
        except sp.CalledProcessError as e:
            print ("command '{}' return with error (code {}): {}"
                   .format(e.cmd, e.returncode, e.output))
            print ('\nUnable to process subject {0} with mask {1}. Please check.'
                   .format(self.raw_data, self.mask))