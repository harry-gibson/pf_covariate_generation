import os, glob
from datetime import date
from dateutil.relativedelta import relativedelta

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

    def __init_(self, Name, DynamicFilenamePattern, SynopticFilenamePattern,
                SpatialSummaryType, TemporalSummaryType, TemporalAnomalyType,
                TemporalLagMonths = 0):
        assert isinstance(SpatialSummaryType, SpatialSummaryTypes)
        assert isinstance(TemporalSummaryType, TemporalAnomalyTypes)
        assert isinstance(TemporalAnomalyType, TemporalAnomalyTypes)
        assert TemporalLagMonths >= 0 and TemporalLagMonths <= 12
        self.Name = Name
        self._DynamicPattern = DynamicFilenamePattern
        self._SynopticPattern = SynopticFilenamePattern
        self._SpatialSummaryType = SpatialSummaryType
        self._TemporalSummaryType = TemporalSummaryType
        self._TemporalAnomalyType = TemporalAnomalyType
        self._TemporalLagMonths = TemporalLagMonths
        self._InitialiseFiles()

    def _InitialiseFiles(self):
        '''attempt to build dictionaries mapping available dates, years, or months to filenames'''
        allDynamicFiles = glob.glob(self._DynamicPattern)
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


    def ReadDataForDate(self, RequiredMonth):
        '''produces an array of data representing the content of the required term for this date

        This takes into account the temporal summary, anomaly, and lag as appropriate for this term'''
        if self._TemporalSummaryType == TemporalSummaryTypes.D_MONTHLY:
            dynamicFilename = self.TryGetMonthlyFileForDate(RequiredMonth)

    def TryGetMonthlyFileForDate(self, RequiredMonth):
        UseMonth = RequiredMonth - self._TemporalLagMonths * ONEMONTH
        if self._AllFilesDict.has_key(UseMonth):
            return self._AllFilesDict[UseMonth]
        else:
            return None

    def TryGetSynopticMonthlyFileForDate(self, RequiredMonth):


