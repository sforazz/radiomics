__author__ = 'fsforazz'

import sys
import argparse
import avid.common.workflow as workflow
from avid.selectors import ActionTagSelector as ATS
from avid.actions.mapR import mapRBatchAction as mapR
from avid.actions.matchR import matchRBatchAction as matchR
from avid.actions.threadingScheduler import ThreadingScheduler
from avid.actions.voxelizer import VoxelizerBatchAction as voxelizer
from core.pipelines.CLGlobalFeatures import FeatureExtractionBatchAction as feature_extraction
import avid.common.artefact.defaultProps as artefactProps
import avid.common.demultiplexer as demux
from core.pipelines.bet import BrainExtractionBatchAction as brain_extraction
import avid.common.artefact as artefact
from avid.selectors import KeyValueSelector


__this__ = sys.modules[__name__]
###############################################################################
# general script settings
###############################################################################

#command line parsing
parser = argparse.ArgumentParser()
parser.add_argument('--parallel', '-p', type=int, default=1)
parser.add_argument('--features', '-f', nargs='+', type=str, default='all',
                    help='features to extract. Possible values are: fo, loci, cooc2, ivoh, vol, volden, ngld, rl, id, ngtd.'
                    'Default = all.')
parser.add_argument('--outputExt', '-e', type=str, default='nrrd',
                    help='Output extention to be used to save all the images results. Possible values'
                    ' are: "nrrd", "nii", "nii.gz". Default = nrrd.')
parser.add_argument('--use_gtv_t1', '-u', action='store_true', default=False)
 
cliargs, unknown = parser.parse_known_args()
multiTaskCount = cliargs.parallel
features = cliargs.features
outputExt = cliargs.outputExt
use_gtv_t1 = cliargs.use_gtv_t1

# artefact.similarityRelevantProperties.append('scan')
###############################################################################
# general setup selectors for a more readable script
###############################################################################
names = ['T1KM', 'T1', 'T2', 'FLAIR', 'ADC', 'SWI']
ReferenceImageSelector = ATS('CT')

# VoxelizerRefSelector = ATS('StructRef')
# VoxelizerStructSelector = ATS('StructSet')
# MovingImageSelector = ATS('MRI') + KeyValueSelector('scan', 'T1KM')

###############################################################################
# the workflow itself
###############################################################################
for name in names:
    if use_gtv_t1:
        MaskImageSelector = ATS('mask')
    else:
        MaskImageSelector = ATS('{}mask'.format(name))
    RefImageSelector = ATS('{}ref'.format(name)) 
    with workflow.initSession_byCLIargs(expandPaths=True, autoSave=True) as session:
    
        feature_Selector = feature_extraction(
            RefImageSelector, MaskImageSelector, same_tp=True, features=features,
            actionTag='{}_feature_ext'.format(name),
            scheduler=ThreadingScheduler(multiTaskCount)).do().tagSelector
