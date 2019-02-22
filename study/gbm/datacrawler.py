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


def fileFunction(pathParts, fileName, fullPath):
    '''Functor to generate an artefact for a file stored with the BAT project
    storage conventions.'''
    result = None
    _, name, ext = split_filename(fileName)
#     name, ext = os.path.splitext(fileName)
    case = pathParts[0] #first dir is case id

    if ext in AVAILABLE_OUT_EXT:
        result = generateArtefactEntry(case, None, 0, name, artefactProps.TYPE_VALUE_RESULT,
                                       artefactProps.FORMAT_VALUE_ITK, fullPath)
    elif ext=='.dcm':
        if pathParts[-2] == 'BPLCT' or pathParts[-2] == 'CT':
            result = generateArtefactEntry(case, None, 0, 'StructRef', artefactProps.TYPE_VALUE_RESULT,
                                           artefactProps.FORMAT_VALUE_ITK, fullPath)
        elif pathParts[-2] == 'RTSTRUCT':
            result = generateArtefactEntry(case, None, 0, 'StructSet', artefactProps.TYPE_VALUE_RESULT,
                                           artefactProps.FORMAT_VALUE_ITK, fullPath)

    return result
  
  
def generateArtefactList(root, inputs):
    crawler = DirectoryCrawler(root, fileFunction, True)
  
    return crawler.getArtefacts()


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', '-r', type=str)
    parser.add_argument('--output', '-o', type=str)
    parser.add_argument('--inputs', '-i', nargs='+', type=str, default=None)

    cliargs, unknown = parser.parse_known_args()

    artefacts = generateArtefactList(cliargs.root, cliargs.inputs)
  
    saveArtefactList(cliargs.output, artefacts)
