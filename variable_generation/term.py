import os, glob
from datetime import date
from dateutil.relativedelta import relativedelta
import sys
sys.path.insert(0, r'C:\Users\zool1301.NDPH\Documents\Code_General\MAP-raster-utilities')

from raster_utilities.utils.geotransform_calcs import CalculatePixelLims
from raster_utilities.cubes.tiff_cube import TiffCube
from raster_utilities.cubes.cube_constants import CubeResolutions, CubeLevels
from raster_utilities.aggregation.aggregation_values import TemporalAggregationStats, ContinuousAggregationStats, \
    CategoricalAggregationStats

ONEMONTH = relativedelta(months=1)

from enum import Enum
class TemporalAnomalyTypes(Enum):
    DIFF_SYNOPTIC_ANNUAL = "Difference from synoptic annual"
    DIFF_SYNOPTIC_MONTHLY = "Difference from synoptic monthly"
    NONE = "None"

class CovariateVariableTerm:
    # Pass a folder "CubeFolder" which should contain a folder structure corresponding to the MAP specification for a
    # mastergrid covariate (See the MAP wiki). It should contain a subfolder corresponding to the chosen resolution and
    # this should contain Annual, Monthly, Synoptic folders, or as necessary for the
    # chosen SpatialSummaryType and TemporalSummaryType.

    # Monthly folder has files with names like {VariableName}.{Year}.{Month}.{TemporalSummary}.{Res}.{SpatialSummary}.tif
    # Annual folder has files with names like {VariableName}.{Year}.Annual.{TemporalSummary}.{Res}.{SpatialSummary}.tif
    # Synoptic folder has files with names like {VariableName}.Synoptic.{Month / Overall}.{Res}.{SpatialSummary}.tif

    def __init__(self, Name, MasterFolder,
                 CubeResolution, CubeLevel,
                 SpatialSummaryStat,
                 TemporalSummaryStat = TemporalAggregationStats.MEAN,
                 TemporalAnomalyType = TemporalAnomalyTypes.NONE,
                 TemporalLagMonths = 0,
                 AdjustmentOffset = 0):
        assert isinstance(CubeResolution, CubeResolutions)
        assert isinstance(CubeLevel, CubeLevels) # Monthly, Annual, Synoptic, Static? General cube descriptor.
        assert (isinstance(SpatialSummaryStat, ContinuousAggregationStats)
                or isinstance(SpatialSummaryStat, CategoricalAggregationStats))# Mean, SD, ...? General cube descriptor.
        assert isinstance(TemporalSummaryStat, TemporalAggregationStats) # Mean, SD, ...? General cube descriptor.

        assert isinstance(TemporalAnomalyType, TemporalAnomalyTypes) # Specific to the Pf covars work
        assert TemporalLagMonths >= 0 and TemporalLagMonths <= 12
        self.Name = Name
        self._CubeResolution = CubeResolution
        self._CubeLevel = CubeLevel
        self._SpatialSummaryStat = SpatialSummaryStat
        self._TemporalSummaryStat = TemporalSummaryStat
        self._TemporalAnomalyType = TemporalAnomalyType
        self._TemporalLagMonths = TemporalLagMonths
        self._AdjustmentOffset = AdjustmentOffset
        self._InitialiseCube(MasterFolder)

    def _InitialiseCube(self, MasterFolder):
        # the cube object will populate itself with whatever is available for temporal summary levels, i.e.
        # monthly, annual, synoptic (any combination) or static
        myCube = TiffCube(MasterFolder, self._CubeResolution, self._TemporalSummaryStat, self._SpatialSummaryStat)
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
        # The Cube object figures out what file to read based on the CubeLevel and the Date (or "None"), including if
        # it's a static variable
        dataArr, _gt, _proj, _ndv = self.DataCube.ReadDataForDate(self._CubeLevel, dataDate)
        # some of the Pf terms are actually calculated in terms of difference between a monthly dynamic value and a
        # long-term average i.e. synoptic.
        # If not, then just return what we've read
        if self._TemporalAnomalyType == TemporalAnomalyTypes.NONE:
            return dataArr
        # If we do neeed to calculate an anomaly, then use the same Cube to provide access to the synoptic data
        # from which this (presumably dynamic) term is differenced against
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






