import os, glob
from datetime import date
from dateutil.relativedelta import relativedelta

from raster_utilities.utils.geotransform_calcs import CalculatePixelLims
from raster_utilities.io.tiff_management import GetRasterProperties, ReadAOI_PixelLims

ONEMONTH = relativedelta(months=1)

class SpatialSummaryTypes:
    MAX = "max"
    MEAN = "mean"
    MIN = "min"
    RANGE = "range"
    SD = "SD"
    FRACTIONAL = "ss_fractionalbinary"

class TemporalSummaryTypes:
    D_MONTHLY = "Dynamic monthly"
    D_ANNUAL = "Dynamic annual"
    S_MONTHLY_MEAN = "Synoptic Monthly Mean"
    S_MONTHLY_SD = "Synoptic Monthly SD"
    S_ANNUAL_MEAN = "Synoptic Annual Mean"
    STATIC = "Static variable"

class TemporalAnomalyTypes:
    DIFF_SYNOPTIC_ANNUAL = "Difference from synoptic annual"
    DIFF_SYNOPTIC_MONTHLY = "Difference from synoptic monthly"
    NONE = "None"


class FiveKCovariateVariableTerm:
    # Pass a folder "MasterFolder" which should contain Annual, Monthly, Synoptic folders, or as necessary for the
    # chosen SpatialSummaryType and TemporalSummaryType.

    # Monthly folder has files with names like {VariableName}.{Year}.{Month}.{TemporalSummary}.{Res}.{SpatialSummary}.tif
    # Annual folder has files with names like {VariableName}.{Year}.Annual.{TemporalSummary}.{Res}.{SpatialSummary}.tif
    # Synoptic folder has files with names like {VariableName}.Synoptic.{Month / Overall}.{Res}.{SpatialSummary}.tif

    def __init__(self, Name, MasterFolder,
                SpatialSummaryType, TemporalSummaryType, TemporalAnomalyType,
                TemporalLagMonths = 0):
        assert isinstance(SpatialSummaryType, SpatialSummaryTypes)
        assert isinstance(TemporalSummaryType, TemporalAnomalyTypes)
        assert isinstance(TemporalAnomalyType, TemporalAnomalyTypes)
        assert TemporalLagMonths >= 0 and TemporalLagMonths <= 12
        self.Name = Name
        self._MasterFolder = MasterFolder
        #self._DynamicPattern = DynamicFilenamePattern
        #self._SynopticPattern = SynopticFilenamePattern
        self._SpatialSummaryType = SpatialSummaryType
        self._TemporalSummaryType = TemporalSummaryType
        self._TemporalAnomalyType = TemporalAnomalyType
        self._TemporalLagMonths = TemporalLagMonths
        self._InitialiseFiles()

    def _InitialiseFiles(self):
        '''attempt to build dictionaries mapping available dates, years, or months to filenames'''

        if self._TemporalSummaryType == TemporalSummaryTypes.D_MONTHLY:
            monthlyFolder = os.path.join(self._MasterFolder, 'Monthly')
            monthlyPattern = os.path.join(monthlyFolder, '*.{0}.tif'.format(self._SpatialSummaryType))
            allDynamicFiles = glob.glob(monthlyPattern)

        allSynopticFiles = glob.glob(self._SynopticPattern)
        dynamicMonthlyDict = {}
        synopticMthDict = {}
        dynamicAnnualDict = {}

        for f in allDynamicFiles:
            fileDate = self.parseDateFromFilepath(f)
            assert not dynamicMonthlyDict.has_key(fileDate)
            dynamicMonthlyDict[fileDate] = f
        for f in allSynopticFiles:
            fileWhatnot = self.parseDateFromFilepath(f)
            if len(fileWhatnot) == 2:
                # synoptic monthly file like "03"
                monthnum = int(fileWhatnot)
                assert not synopticMthDict.has_key(monthnum)
                synopticMthDict[monthnum] = f
            elif len(fileWhatnot) == 4:
                yearnum = int(fileWhatnot)
                assert not dynamicAnnualDict.has_key(yearnum)
                dynamicAnnualDict[yearnum] = f
        if self._TemporalSummaryType == TemporalSummaryTypes.D_MONTHLY:
            self.DynamicMonthlyFiles = dynamicMonthlyDict
        if self._TemporalSummaryType == TemporalSummaryTypes.D_ANNUAL:
            self.DynamicAnnualFiles = dynamicAnnualDict
        if (self._TemporalSummaryType == TemporalSummaryTypes.S_MONTHLY_MEAN or
            self._TemporalSummaryType == TemporalSummaryTypes.S_MONTHLY_SD or
            self._TemporalAnomalyType == TemporalAnomalyTypes.DIFF_SYNOPTIC_MONTHLY):
            self.SynopticMonthlyFiles = synopticMthDict


    def parseDateFromFilepath(self, fullPath):
        '''attempt to parse MODIS cube filenames in the format used by MAP

        Returns either a Date, or a string with length 4 (a year) or a string with length 2 (a month)'''
        parts = fullPath.split('.')
        yrOrNot = parts[1]
        mthOrNot = parts[2]
        try:
            try:
                yr = int(yrOrNot)
                mth = int(mthOrNot)
                if yr >= 1900 and mth <= 12:
                    return date(yr, mth, 1)
            except ValueError:
                yr = int(yrOrNot)
                return str(yr)
        except ValueError:
            mth = int(mthOrNot)
            return str(mth).zfill(2)


    def ReadDataForDate(self, RequiredDate):
        '''produces an array of data representing the content of the required term for this date

        This takes into account the temporal summary, anomaly, and lag as appropriate for this term

        TODO - specify a subset bounding box'''
        rasterFilename = None
        if self._TemporalSummaryType == TemporalSummaryTypes.D_MONTHLY:
            rasterFilename = self.TryGetMonthlyFileForDate(RequiredDate)
        elif self._TemporalSummaryType == TemporalSummaryTypes.D_ANNUAL:
            rasterFilename = self.TryGetAnnualFileForDate(RequiredDate)
        elif (self._TemporalSummaryType == TemporalSummaryTypes.S_MONTHLY_SD or
            self._TemporalSummaryType == TemporalSummaryTypes.S_MONTHLY_MEAN):
            rasterFilename = self.TryGetSynopticMonthlyFileForDate()
        elif (self._TemporalSummaryType == TemporalSummaryTypes.S_ANNUAL_MEAN or
            self._TemporalSummaryType == TemporalSummaryTypes.STATIC):
            rasterFilename = self.StaticFilename

        if rasterFilename:
            dataArr, dataGT, dataProj, dataNDV = ReadAOI_PixelLims(rasterFilename)
            return dataArr
        else:
            assert False





    def TryGetMonthlyFileForDate(self, RequiredDate):
        UseMonth = RequiredDate - self._TemporalLagMonths * ONEMONTH
        if self.DynamicMonthlyFiles.has_key(UseMonth):
            return self.DynamicMonthlyFiles[UseMonth]
        else:
            return None

    def TryGetAnnualFileForDate(self, RequiredDate):
        # no lag involved with dynamic annual variables
        UseYear = RequiredDate.year
        if self.DynamicAnnualFiles.has_key(UseYear):
            return self.DynamicAnnualFiles[UseYear]
        else:
            return None

    def TryGetSynopticMonthlyFileForDate(self, RequiredDate):
        UseMonth = RequiredDate.month
        if self.SynopticMonthlyFiles.has_key(UseMonth):
            return self.SynopticMonthlyFiles[UseMonth]
        else:
            return None




