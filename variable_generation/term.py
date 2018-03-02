import os, glob
from datetime import date
from dateutil.relativedelta import relativedelta

from raster_utilities.utils.geotransform_calcs import CalculatePixelLims
from raster_utilities.io.tiff_management.tiff_cube import TiffCube, CubeResolutions, CubeLevels
from raster_utilities.aggregation.aggregation_values import TemporalAggregationStats, ContinuousAggregationStats

ONEMONTH = relativedelta(months=1)


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

    def __init__(self, Name, MasterFolder, CubeLevel, SpatialSummaryType,
                    TemporalSummaryType = TemporalAggregationStats.MEAN,
                    TemporalAnomalyType = TemporalAnomalyTypes.NONE,
                    TemporalLagMonths = 0):
        assert isinstance(CubeLevel, CubeLevels) # Monthly, Annual, Synoptic, Static? General cube descriptor.
        assert isinstance(SpatialSummaryType, ContinuousAggregationStats) # Mean, SD, ...? General cube descriptor.
        assert isinstance(TemporalSummaryType, TemporalAggregationStats) # Mean, SD, ...? General cube descriptor.

        assert isinstance(TemporalAnomalyType, TemporalAnomalyTypes) # Specific to the Pf covars work
        assert TemporalLagMonths >= 0 and TemporalLagMonths <= 12
        self.Name = Name

        self._CubeLevel = CubeLevel
        self._SpatialSummaryType = SpatialSummaryType
        self._TemporalSummaryType = TemporalSummaryType
        self._TemporalAnomalyType = TemporalAnomalyType
        self._TemporalLagMonths = TemporalLagMonths
        self._InitialiseCube(MasterFolder)

    def _InitialiseCube(self, MasterFolder):
        myCube = TiffCube(MasterFolder, CubeResolutions.FIVE_K, self._TemporalSummaryType, self._SpatialSummaryType)
        self.DataCube = myCube

    def GetOffsetDate(self, RequiredOutputDate):
        if RequiredOutputDate is None:
            return None
        DataMonth = RequiredOutputDate - self._TemporalLagMonths * ONEMONTH
        return DataMonth

    def ReadDataForDate(self, RequiredDate):
        '''produces an array of data representing the content of the required term for this date

        This takes into account the temporal summary, anomaly, and lag as appropriate for this term.
        Date may be None if CubeLevel is synoptic, in which case the overall synoptic data will be read
        '''

        dataDate = self.GetOffsetDate(RequiredDate)
        # The Cube object figures out what file to read based on the CubeLevel and the Date (or "None")
        dataArr, _gt, _proj, _ndv = self.DataCube.ReadDataForDate(self._CubeLevel, dataDate)
        if self._TemporalAnomalyType == TemporalAnomalyTypes.NONE:
            return dataArr

        # The same Cube provides access to the synoptic data from which this (presumably dynamic) term is
        # differenced against
        elif self._TemporalAnomalyType == TemporalAnomalyTypes.DIFF_SYNOPTIC_MONTHLY:
            secondaryArray = self.DataCube.ReadDataForDate(CubeLevels.SYNOPTIC, dataDate)
        elif self._TemporalAnomalyType == TemporalAnomalyTypes.DIFF_SYNOPTIC_ANNUAL:
            secondaryArray = self.DataCube.ReadDataForDate(CubeLevels.SYNOPTIC, None)
        else:
            raise ValueError("Unknown temporal anomaly")
        AnomalyData = dataArr - secondaryArray
        return AnomalyData

        #if self._CubeLevel == CubeLevels.MONTHLY:
        #    self.DataCube.ReadDataForDate(CubeLevels.MONTHLY, dataDate)
        #elif self._CubeLevel == CubeLevels.ANNUAL:
        #    self.DataCube.ReadDataForDate(CubeLevels.ANNUAL, dataDate)
        #elif self._CubeLevel == CubeLevels.SYNOPTIC:
        #    self.DataCube.ReadDataForDate(CubeLevels.SYNOPTIC, dataDate)






