#!/usr/bin/env python3.6
"""
Script to extract multiple features using MitkCLGlobalImageFeatures function.
It assumes that you have already created the artifact object using the datacrawler function and that you pass it as
--sessionPath. 
Its own inputs are:
    - parallel: the number of cores to use (default is 1).
    - resampling: Float number that can be specified if you want to isotropically resample both the raw data 
                  and the mask before extracting the features. Default is None.
    - features: here you can specify a list of features to calculate. The available are:
        -fo: first order features
        -loci: local intensity featrues
        -volden: volume density features
        -ivoh: intensity-volume histogram features
        -vol: volumetric features
        -id: image description features
        -cooc2: co-occurence based features
        -ngld: neighbouring-grey-level-dependence features
        -ngtd: neighbourhood-grey-tone-difference features
        -rl: run-length features
      By default, it calculates all of them. See MITK webpage for more information.
Output:
    One .csv file per subject spcified in the artifact object.

"""
import sys
import argparse
import avid.common.workflow as workflow
from avid.selectors import ActionTagSelector as ATS
from avid.actions.CLGlobalFeatures import FeatureExtractionBatchAction as feature_extraction
from avid.actions.threadingScheduler import ThreadingScheduler

__this__ = sys.modules[__name__]
__author__ = 'fsforazz'
###############################################################################
# general script settings
###############################################################################

#command line parsing
parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('--parallel', '-p', type=int, default=1, help='Number of cores to use. Default=1')
parser.add_argument('--features', '-f', nargs='+', type=str, default='all',
                    help='features to extract. Possible values are: fo, loci, cooc2, ivoh, vol, volden, ngld, rl, id, ngtd.'
                    'Default = all.')
parser.add_argument('--resampling', '-rs', type=float, default=None, help='If provided, both the raw data '
                    'and the segmented mask will be resampled to have isotropic resolution specified by this number. '
                    'By default the original image size will be used.')
   
cliargs, unknown = parser.parse_known_args()
multiTaskCount = cliargs.parallel
features = cliargs.features
resampling = cliargs.resampling
# sespath = '/home/fsforazz/Desktop/mouse_data'

###############################################################################
# general setup selectors for a more readable script
###############################################################################
ImageSelector = ATS('RAW')
maskSelector = ATS('MASK')

###############################################################################
# the workflow itself
###############################################################################

with workflow.initSession_byCLIargs(expandPaths=True, autoSave=True) as session:

    feature_Selector = feature_extraction(ImageSelector, maskSelector, features=features, resampling=resampling,
                                          actionTag = "Features_extraction",
                                          scheduler = ThreadingScheduler(multiTaskCount)).do().tagSelector
        