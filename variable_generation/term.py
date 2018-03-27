import os, glob
from datetime import date
from dateutil.relativedelta import relativedelta
import sys
import numexpr as ne
sys.path.insert(0, r'C:\Users\zool1301.NDPH\Documents\Code_General\MAP-raster-utilities')

from raster_utilities.utils.geotransform_calcs import CalculatePixelLims
from raster_utilities.cubes.tiff_cube import TiffCube
from raster_utilities.cubes.cube_constants import CubeResolutions, CubeLevels
from raster_utilities.aggregation.aggregation_values import TemporalAggregationStats, ContinuousAggregationStats, \
    CategoricalAggregationStats
from transforms import TransformAndAdjust
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
                 AdjustmentOffset = 0,
                 Transform = None):

        # cast string representation e.g. from CSV parsing to the appropriate types (or raise ValueError)
        if not isinstance(CubeResolution, CubeResolutions):
            # resolution, corresponding to a legal folder name i.e. "1km", "5km", "10km" or "500m"
            CubeResolution = CubeResolutions(CubeResolution)
        if not isinstance(CubeLevel, CubeLevels):
            # Monthly, Annual, Synoptic, Static? General cube descriptor.
            CubeLevel = CubeLevels(CubeLevel)
        if not (isinstance(SpatialSummaryStat, ContinuousAggregationStats)
                or isinstance(SpatialSummaryStat, CategoricalAggregationStats)):
            # Mean, SD, ...? General cube descriptor used to pick which spatial summary we are looking at in
            # filtering files
            try:
                SpatialSummaryStat = ContinuousAggregationStats(SpatialSummaryStat)
            except ValueError as e:
                try:
                    SpatialSummaryStat = CategoricalAggregationStats(SpatialSummaryStat)
                except ValueError:
                    raise ValueError(str(SpatialSummaryStat) + " is not a valid continuous or categorical aggregation")
        if not isinstance(TemporalSummaryStat, TemporalAggregationStats):
            # Mean, SD, ...? General cube descriptor used to pick which temporal summary we are looking at in
            # choosing a folder; for the Pf covariates work this is currently always mean for dynamic covars
            TemporalSummaryStat = TemporalAggregationStats(TemporalSummaryStat)
        if not isinstance(TemporalAnomalyType, TemporalAnomalyTypes):
            # Specific to the Pf covars work, are we looking at dynamic values or the difference between dynamic
            # values and some long-term summary of them
            TemporalAnomalyType = TemporalAnomalyTypes(TemporalAnomalyType)
        if not isinstance(TemporalLagMonths, int):
            TemporalLagMonths = int(TemporalLagMonths)
        if not (TemporalLagMonths >= 0 and TemporalLagMonths <= 12):
            raise ValueError("Lag must be between 0 and 12 months (integer)")
        if not (Transform is None or isinstance(Transform, TransformAndAdjust)):
            raise ValueError("If a tranform is provided it must be an instance of the TransformAndAdjust type")

        self.Name = Name
        self._CubeResolution = CubeResolution
        self._CubeLevel = CubeLevel
        self._SpatialSummaryStat = SpatialSummaryStat
        self._TemporalSummaryStat = TemporalSummaryStat
        self._TemporalAnomalyType = TemporalAnomalyType
        self._TemporalLagMonths = TemporalLagMonths
        self._AdjustmentOffset = AdjustmentOffset
        self._Transformer = Transform
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



    def ReadDataForDate(self, RequiredDate, maskNoData=False):
        '''produces an array of data representing the content of the required term for this date

        This takes into account the temporal summary, anomaly, and lag as appropriate for this term.
        These are applied in the following order:
        1: read data, 2: apply anomaly if required, 3: apply offset, 4: apply transform
        Date may be None if CubeLevel is synoptic, in which case the overall synoptic data will be read.

        '''

        dataDate = self.GetOffsetDate(RequiredDate)
        # The Cube object figures out what file to read based on the CubeLevel and the Date (or "None"), including if
        # it's a static variable
        dataArr, _gt, _proj, _ndv = self.DataCube.ReadDataForDate(self._CubeLevel, dataDate, maskNoData=maskNoData)
        # some of the Pf terms are actually calculated in terms of difference between a monthly dynamic value and a
        # long-term average i.e. synoptic.
        # If not, then just return what we've read
        isAnomaly = True
        if self._TemporalAnomalyType == TemporalAnomalyTypes.NONE:
            isAnomaly = False
        # If we do neeed to calculate an anomaly, then use the same Cube to provide access to the synoptic data
        # from which this (presumably dynamic) term is differenced against

        elif self._TemporalAnomalyType == TemporalAnomalyTypes.DIFF_SYNOPTIC_MONTHLY:
            secondaryArray, _, _, _ = self.DataCube.ReadDataForDate(CubeLevels.SYNOPTIC, dataDate, maskNoData=maskNoData)
        elif self._TemporalAnomalyType == TemporalAnomalyTypes.DIFF_SYNOPTIC_ANNUAL:
            secondaryArray, _, _, _ = self.DataCube.ReadDataForDate(CubeLevels.SYNOPTIC, None, maskNoData=maskNoData)
        else:
            raise ValueError("Unknown temporal anomaly")
        expr = "(dataArr)"
        if isAnomaly:
            expr = "(" + expr + " - secondaryArray)"
        if self._AdjustmentOffset != 0:
            adj = self._AdjustmentOffset
            expr = "(" + expr + " + adj)"
        readyToTransform = ne.evaluate(expr)
        if self._Transformer is None:
            return readyToTransform
        return self._Transformer.Apply(readyToTransform)

        #if self._CubeLevel == CubeLevels.MONTHLY:
        #    self.DataCube.ReadDataForDate(CubeLevels.MONTHLY, dataDate)
        #elif self._CubeLevel == CubeLevels.ANNUAL:
        #    self.DataCube.ReadDataForDate(CubeLevels.ANNUAL, dataDate)
        #elif self._CubeLevel == CubeLevels.SYNOPTIC:
        #    self.DataCube.ReadDataForDate(CubeLevels.SYNOPTIC, dataDate)






