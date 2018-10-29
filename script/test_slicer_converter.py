from converters.dcm_converters import DicomConverters


filename = ('/home/fsforazz/Desktop/PhD_project/fibrosis_project/Tr6_19w_CT/Tr6_20W_1/TR6_20WK_RT1_RT_alone/2/'
            'TR6_20W_RT1_RADIATION_ALONE_MAHMOUD.CT.SPEZIAL_CHENG_CT_MOUSE_(ERWACHSENER).0002.0001.2016.03.22.17.'
            '38.19.781250.363611330.IMA')
converter = DicomConverters(filename)
converter.slicer_converter()

print 'Done!'