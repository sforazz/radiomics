__author__ = 'fsforazz'

import sys
import argparse
import avid.common.workflow as workflow
from avid.selectors import ActionTagSelector as ATS
from avid.actions.mapR import mapRBatchAction as mapR
from avid.actions.matchR import matchRBatchAction as matchR
from avid.actions.invertR import invertRBatchAction as invertR
from avid.actions.threadingScheduler import ThreadingScheduler

__this__ = sys.modules[__name__]

###############################################################################
# general script settings
###############################################################################

#command line parsing
parser = argparse.ArgumentParser()
parser.add_argument('--regAlg', '-a', type=str)
parser.add_argument('--parallel', '-p', type=int, default=1)
 
cliargs, unknown = parser.parse_known_args()
multiTaskCount = cliargs.parallel
regAlgPath = cliargs.regAlg

# regAlgPath = '/home/fsforazz/git/MITK-superbuild/MITK-build/lib/mdra-D-0-13_MITK_MultiModal_rigid_default.so'
###############################################################################
# general setup selectors for a more readable script
###############################################################################
ReferenceImageSelector = ATS('BPLCT')
GTVImageSelector = ATS('GTV')

###############################################################################
# the workflow itself
###############################################################################
for i in range(2):

    if i == 0:
        MovingImageSelector = ATS('PlanningMRI')
        reg_actionTag = 'PMRI2CT'
        map_actionTag = 'mapped_PMRI'
        invert_actionTag = 'invert_PMRI'
        gtv_actionTag = 'mapped_GTV2PMRI'
    elif i == 1:
        MovingImageSelector = ATS('FUMRI')
        reg_actionTag = 'FUMRI2CT'
        map_actionTag = 'mapped_FUMRI'
        invert_actionTag = 'invert_FUMRI'
        gtv_actionTag = 'mapped_GTV2FUMRI'

    with workflow.initSession_byCLIargs(expandPaths=True, autoSave=True) as session:
    
        reg_Selector = matchR(
            ReferenceImageSelector, MovingImageSelector, targetIsReference = False, algorithm=regAlgPath,
            actionTag = reg_actionTag, scheduler=ThreadingScheduler(multiTaskCount)).do().tagSelector
    
        mapped_moving_selector = mapR(
            MovingImageSelector, reg_Selector, ReferenceImageSelector, actionTag=map_actionTag,
            scheduler=ThreadingScheduler(multiTaskCount)).do().tagSelector
        
        invertR_selector = invertR(
            reg_Selector, actionTag=invert_actionTag,
            scheduler=ThreadingScheduler(multiTaskCount)).do().tagSelector
        
        mapped_inverse_selector = mapR(
            GTVImageSelector, invertR_selector, MovingImageSelector, actionTag=gtv_actionTag,
            scheduler=ThreadingScheduler(multiTaskCount)).do().tagSelector
