__author__ = 'floca'

import os
import argparse

from avid.common.artefact.crawler import DirectoryCrawler
import avid.common.artefact.defaultProps as artefactProps
from avid.common.artefact.generator import generateArtefactEntry
from avid.common.artefact.fileHelper import saveArtefactList_xml as saveArtefactList
from avid.common.artefact import similarityRelevantProperties

similarityRelevantProperties.append('sequence')

def fileFunction(pathParts, fileName, fullPath):
    '''Functor to generate an artefact for a file stored with the BAT project
    storage conventions.'''
    result = None
    name, ext = os.path.splitext(fileName)
    case = pathParts[0] #first dir is case id

    if ext=='.nrrd':
        if name.startswith('Raw') and name.endswith('cropped'):
            result = generateArtefactEntry(case, None, 0, 'RAW', artefactProps.TYPE_VALUE_RESULT,
                                           artefactProps.FORMAT_VALUE_ITK, fullPath)
        elif not name.startswith('Raw') and name.endswith('cropped'):
            result = generateArtefactEntry(case, None, 0, 'MASK', artefactProps.TYPE_VALUE_RESULT,
                                           artefactProps.FORMAT_VALUE_ITK, fullPath)

        elif name.startswith('Raw') and not name.endswith('cropped'):
            result = generateArtefactEntry(case, None, 0, 'RAW', artefactProps.TYPE_VALUE_RESULT,
                                           artefactProps.FORMAT_VALUE_ITK, fullPath)
        elif not name.startswith('Raw') and not name.endswith('cropped'):
            result = generateArtefactEntry(case, None, 0, 'MASK', artefactProps.TYPE_VALUE_RESULT,
                                           artefactProps.FORMAT_VALUE_ITK, fullPath)

    return result
  
  
def generateArtefactList(root):
    crawler = DirectoryCrawler(root, fileFunction, True)
    
    return crawler.getArtefacts()
    
    
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument('root')
    parser.add_argument('output')
    
    cliargs, unknown = parser.parse_known_args()
    
    artefacts = generateArtefactList(cliargs.root)
    
    saveArtefactList(cliargs.output, artefacts)
