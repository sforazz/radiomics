__author__ = 'fsforazz'

import argparse

from avid.common.artefact.crawler import DirectoryCrawler
import avid.common.artefact.defaultProps as artefactProps
from avid.common.artefact.generator import generateArtefactEntry
from avid.common.artefact.fileHelper import saveArtefactList_xml as saveArtefactList
from avid.common.artefact import similarityRelevantProperties
from core.utils.filemanip import split_filename
import glob

similarityRelevantProperties.append('sequence')
AVAILABLE_OUT_EXT = ['.nii.gz']
# tp_dict = {}
# tp_dict['CT'] = 0
# tp_dict['T1'] = 1
# tp_dict['T1KM'] = 2
# tp_dict['T2'] = 3
# tp_dict['FLAIR'] = 4
# tp_dict['ADC'] = 5
# tp_dict['SWI'] = 6


def fileFunction(pathParts, fileName, fullPath):
    '''Functor to generate an artefact for a file stored with the BAT project
    storage conventions.'''
    result = []
    _, name, ext = split_filename(fileName)
    modality = pathParts[0].split('_')[0]
    if ext in AVAILABLE_OUT_EXT:
        if pathParts[-1] != 'volumina' and 'CT' not in pathParts and 'ica_results' not in pathParts:
            case = pathParts[-1]
            try:
                tp = name.split('#')[1].split('_')[0]
            except:
                print('Problem')
            result = generateArtefactEntry(case, None, tp, '{}ref'.format(modality), artefactProps.TYPE_VALUE_RESULT,
                                           artefactProps.FORMAT_VALUE_ITK, fullPath)
        elif pathParts[-1] == 'volumina' and 'CT' not in pathParts[0] and 'ica_results' not in pathParts:
            case = pathParts[-2]
            tp = name.split('.')[0].split('_')[1]
            result = generateArtefactEntry(case, None, tp, '{}mask'.format(modality), artefactProps.TYPE_VALUE_RESULT,
                                           artefactProps.FORMAT_VALUE_ITK, fullPath)

    return result


def fileFunction2(pathParts, fileName, fullPath):
    '''Functor to generate an artefact for a file stored with the BAT project
    storage conventions.'''
    result = []
    _, name, ext = split_filename(fileName)
    modality = pathParts[0].split('_')[0]
    if ext in AVAILABLE_OUT_EXT:
        if pathParts[-1] != 'volumina' and 'CT' not in pathParts and 'ica_results' not in pathParts:
            case = pathParts[-1]
            try:
                tp = name.split('#')[1].split('_')[0]
            except:
                print('Problem')
            result = generateArtefactEntry(case, None, tp, '{}ref'.format(modality), artefactProps.TYPE_VALUE_RESULT,
                                           artefactProps.FORMAT_VALUE_ITK, fullPath)
        elif (pathParts[-1] == 'volumina' and 'CT' not in pathParts[0] and 'ica_results' not in pathParts
                and 'T1KM_MRI_mapped' in pathParts):
            case = pathParts[-2]
            tp = name.split('.')[0].split('_')[1]
            result = generateArtefactEntry(case, None, tp, 'mask', artefactProps.TYPE_VALUE_RESULT,
                                           artefactProps.FORMAT_VALUE_ITK, fullPath)

    return result

  
def generateArtefactList(root, use_gtv_t1=False):
    if use_gtv_t1:
        crawler = DirectoryCrawler(root, fileFunction2, True)
    else:
        crawler = DirectoryCrawler(root, fileFunction, True)
  
    return crawler.getArtefacts()


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', '-r', type=str)
    parser.add_argument('--output', '-o', type=str)
    parser.add_argument('--use_gtv_t1', '-u', action='store_true', default=False)

    cliargs, unknown = parser.parse_known_args()

    artefacts = generateArtefactList(cliargs.root, use_gtv_t1=cliargs.use_gtv_t1)
  
    saveArtefactList(cliargs.output, artefacts)

    print('Done!')
