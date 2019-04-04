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


__this__ = sys.modules[__name__]
###############################################################################
# general script settings
###############################################################################

#command line parsing
parser = argparse.ArgumentParser()
parser.add_argument('--regAlg', '-a', type=str)
parser.add_argument('--device', '-d', type=str, default='0', 
                    help='used to set on which device the brain extraction will run. 0 for GPU, "cpu" for CPU.'
                    'Default is CPU.')
parser.add_argument('--parallel', '-p', type=int, default=1)
parser.add_argument('--structures', '-s', nargs='+', type=str, default=None)
parser.add_argument('--features', '-f', nargs='+', type=str, default='all',
                    help='features to extract. Possible values are: fo, loci, cooc2, ivoh, vol, volden, ngld, rl, id, ngtd.'
                    'Default = all.')
parser.add_argument('--outputExt', '-e', type=str, default='nrrd',
                    help='Output extention to be used to save all the images results. Possible values'
                    ' are: "nrrd", "nii", "nii.gz". Default = nrrd.')
 
cliargs, unknown = parser.parse_known_args()
multiTaskCount = cliargs.parallel
regAlgPath = cliargs.regAlg
structures = cliargs.structures
features = cliargs.features
outputExt = cliargs.outputExt
device = cliargs.device

###############################################################################
# general setup selectors for a more readable script
###############################################################################

ReferenceImageSelector = ATS('CT')

VoxelizerRefSelector = ATS('StructRef')
VoxelizerStructSelector = ATS('StructSet')
MovingImageSelector = ATS('MRI')

###############################################################################
# the workflow itself
###############################################################################
    
with workflow.initSession_byCLIargs(expandPaths=True, autoSave=True) as session:

    reg_Selector = matchR(
        ReferenceImageSelector, MovingImageSelector, targetIsReference=False, algorithm=regAlgPath,
        actionTag='MRI_reg', scheduler=ThreadingScheduler(multiTaskCount)).do().tagSelector
        
    bet_Selector = brain_extraction(
        MovingImageSelector, device=device,
        actionTag='MRI_bet', scheduler=ThreadingScheduler(1)).do().tagSelector

    mapped_moving_selector = mapR(
        MovingImageSelector, reg_Selector, ReferenceImageSelector, actionTag='MRI_mapped',
        scheduler=ThreadingScheduler(multiTaskCount), outputExt=outputExt).do().tagSelector
    
    mask_selector = demux.getSelectors(artefactProps.RESULT_SUB_TAG, bet_Selector)['MASK']
    mapped_bet_mask = mapR(
        mask_selector, reg_Selector, ReferenceImageSelector, interpolator = "nn", actionTag='MRI_bet_mapped',
        scheduler=ThreadingScheduler(multiTaskCount), outputExt=outputExt).do().tagSelector
    
    voxelizer_selector = voxelizer(
        VoxelizerStructSelector, VoxelizerRefSelector, structNames = structures,
        booleanMask = True, actionTag='voxelizer', outputExt=outputExt,
        scheduler=ThreadingScheduler(multiTaskCount)).do().tagSelector

    if outputExt != 'nrrd':
        map_mask2image_selector = mapR(
            voxelizer_selector, templateSelector=ReferenceImageSelector, interpolator = "nn",
            actionTag='map_mask2Ref', scheduler=ThreadingScheduler(multiTaskCount),
            outputExt=outputExt).do().tagSelector

        feature_Selector = feature_extraction(
            mapped_moving_selector, map_mask2image_selector, same_tp=False, features=features,
            actionTag='MRI_feature_ext',
            scheduler=ThreadingScheduler(multiTaskCount)).do().tagSelector
    else:
        feature_Selector = feature_extraction(
            mapped_moving_selector, voxelizer_selector, features=features,
            actionTag='MRI_feature_ext',
            scheduler=ThreadingScheduler(multiTaskCount)).do().tagSelector
