__author__ = 'fsforazz'

import argparse

from avid.common.artefact.crawler import DirectoryCrawler
import avid.common.artefact.defaultProps as artefactProps
from avid.common.artefact.generator import generateArtefactEntry
from avid.common.artefact.fileHelper import saveArtefactList_xml as saveArtefactList
from avid.common.artefact import similarityRelevantProperties
from core.utils.filemanip import split_filename

similarityRelevantProperties.append('sequence')
AVAILABLE_OUT_EXT = ['.nrrd', '.nii', '.nii.gz']
tp_dict = {}
tp_dict['CT'] = 0
tp_dict['MR_T1'] = 1
tp_dict['MR_T1KM'] = 2
tp_dict['MR_T2'] = 3
tp_dict['MR_FLAIR'] = 4

def fileFunction(pathParts, fileName, fullPath):
    '''Functor to generate an artefact for a file stored with the BAT project
    storage conventions.'''
    result = None
    _, name, ext = split_filename(fileName)
#     name, ext = os.path.splitext(fileName)
    case = pathParts[0] #first dir is case id

    if ext in AVAILABLE_OUT_EXT:
        if name == 'CT':
            result = generateArtefactEntry(case, None, 0, name, artefactProps.TYPE_VALUE_RESULT,
                                           artefactProps.FORMAT_VALUE_ITK, fullPath)
        else:
            try:
                result = generateArtefactEntry(case, None, tp_dict[name], 'MRI', artefactProps.TYPE_VALUE_RESULT,
                                               artefactProps.FORMAT_VALUE_ITK, fullPath)
            except KeyError:
                pass
    elif ext=='.dcm':
        if pathParts[-1] == 'CT':
            result = generateArtefactEntry(case, None, 0, 'StructRef', artefactProps.TYPE_VALUE_RESULT,
                                           artefactProps.FORMAT_VALUE_ITK, fullPath)
        elif pathParts[-1] == 'RTSTRUCT':
            result = generateArtefactEntry(case, None, 0, 'StructSet', artefactProps.TYPE_VALUE_RESULT,
                                           artefactProps.FORMAT_VALUE_ITK, fullPath)

    return result
  
  
def generateArtefactList(root):
    crawler = DirectoryCrawler(root, fileFunction, True)
  
    return crawler.getArtefacts()


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', '-r', type=str)
    parser.add_argument('--output', '-o', type=str)

    cliargs, unknown = parser.parse_known_args()

    artefacts = generateArtefactList(cliargs.root)
  
    saveArtefactList(cliargs.output, artefacts)
