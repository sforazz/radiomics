__author__ = 'fsforazz'

import sys
import argparse
import avid.common.workflow as workflow
from avid.selectors import ActionTagSelector as ATS
from avid.actions.mapR import mapRBatchAction as mapR
from avid.actions.matchR import matchRBatchAction as matchR
from avid.actions.threadingScheduler import ThreadingScheduler
from avid.actions.voxelizer import VoxelizerBatchAction as voxelizer
from avid.actions.CLGlobalFeatures import FeatureExtractionBatchAction as feature_extraction

__this__ = sys.modules[__name__]

###############################################################################
# general script settings
###############################################################################

#command line parsing
parser = argparse.ArgumentParser()
parser.add_argument('--regAlg', '-a', type=str)
parser.add_argument('--parallel', '-p', type=int, default=1)
parser.add_argument('--structures', '-s', nargs='+', type=str, default=None)
parser.add_argument('--features', '-f', nargs='+', type=str, default='all',
                    help='features to extract. Possible values are: fo, loci, cooc2, ivoh, vol, volden, ngld, rl, id, ngtd.'
                    'Default = all.')
parser.add_argument('--resampling', '-rs', type=float, default=None, help='If provided, both the raw data '
                    'and the segmented mask will be resampled to have isotropic resolution specified by this number. '
                    'By default the original image size will be used.')
 
cliargs, unknown = parser.parse_known_args()
multiTaskCount = cliargs.parallel
regAlgPath = cliargs.regAlg
structures = cliargs.structures
features = cliargs.features
resampling = cliargs.resampling

# regAlgPath = '/home/fsforazz/git/MITK-superbuild/MITK-build/lib/mdra-D-0-13_MITK_MultiModal_rigid_default.so'
###############################################################################
# general setup selectors for a more readable script
###############################################################################
ReferenceImageSelector = ATS('BPLCT')
VoxelizerRefSelector = ATS('StructRef')
VoxelizerStructSelector = ATS('StructSet')

###############################################################################
# the workflow itself
###############################################################################
for i in range(2):

    if i == 0:
        MovingImageSelector = ATS('PlanningMRI')
        reg_actionTag = 'PMRI2CT'
        map_actionTag = 'mapped_PMRI'
        feature_actionTag = 'feature_ext_PMRI'
    elif i == 1:
        MovingImageSelector = ATS('FUMRI')
        reg_actionTag = 'FUMRI2CT'
        map_actionTag = 'mapped_FUMRI'
        feature_actionTag = 'feature_ext_FUMRI'

    with workflow.initSession_byCLIargs(expandPaths=True, autoSave=True) as session:
    
        reg_Selector = matchR(
            ReferenceImageSelector, MovingImageSelector, targetIsReference = False, algorithm=regAlgPath,
            actionTag = reg_actionTag, scheduler=ThreadingScheduler(multiTaskCount)).do().tagSelector
    
        mapped_moving_selector = mapR(
            MovingImageSelector, reg_Selector, ReferenceImageSelector, actionTag=map_actionTag,
            scheduler=ThreadingScheduler(multiTaskCount)).do().tagSelector
        
        voxelizer_selector = voxelizer(
            VoxelizerStructSelector, VoxelizerRefSelector, structNames = structures,
            booleanMask = True, actionTag='voxelizer',
            scheduler=ThreadingScheduler(multiTaskCount)).do().tagSelector
        
        feature_Selector = feature_extraction(
            mapped_moving_selector, voxelizer_selector, features=features, resampling=resampling,
            actionTag=feature_actionTag,
            scheduler=ThreadingScheduler(multiTaskCount)).do().tagSelector
