import glob, os
class TiffCubeReader:
    # defines the properties of a "cube" of geotiff files, i.e. a folder full of files representing a single
    # variable at a given spatial and temporal resolution.

    __month_expr__ = "yyyy.mm"
    def __init__(self, variableName, spatialSummary, temporalSummary, filenameWildcard):
        self.variableName = variableName
        self.spatialSummary = spatialSummary
        self.temporalSummary = temporalSummary
        self.filePattern = filenameWildcard
        self.__dynamicMonthDict__ = {}
        self.__synopticMonthDict__ = {}
        self.__synopticYearDict__ = {}

    def buildDictionaries(self):
        allfiles = glob.glob(self.filePattern)



    def getFileName(self, nominalDate = None):
        # returns
        if self.temporalSummary != "Synoptic":
            raise Exception

