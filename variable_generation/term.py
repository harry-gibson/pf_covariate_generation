import os, glob
from datetime import date
from dateutil.relativedelta import relativedelta
import sys
import numexpr as ne
import numpy
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
                 SpatialSummaryType,
                 TemporalSummaryType = TemporalAggregationStats.MEAN,
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
        if not (isinstance(SpatialSummaryType, ContinuousAggregationStats)
                or isinstance(SpatialSummaryType, CategoricalAggregationStats)):
            # Mean, SD, ...? General cube descriptor used to pick which spatial summary we are looking at in
            # filtering files
            try:
                SpatialSummaryType = ContinuousAggregationStats(SpatialSummaryType)
            except ValueError as e:
                try:
                    SpatialSummaryType = CategoricalAggregationStats(SpatialSummaryType)
                except ValueError:
                    raise ValueError(str(SpatialSummaryType) + " is not a valid continuous or categorical aggregation")
        if not isinstance(TemporalSummaryType, TemporalAggregationStats):
            # Mean, SD, ...? General cube descriptor used to pick which temporal summary we are looking at in
            # choosing a folder; for the Pf covariates work this is currently always mean for dynamic covars
            TemporalSummaryType = TemporalAggregationStats(TemporalSummaryType)
        if not isinstance(TemporalAnomalyType, TemporalAnomalyTypes):
            # Specific to the Pf covars work, are we looking at dynamic values or the difference between dynamic
            # values and some long-term summary of them
            try:
                TemporalAnomalyType = TemporalAnomalyTypes(TemporalAnomalyType)
            except ValueError:
                TemporalAnomalyType = TemporalAnomalyTypes.NONE
        if not isinstance(TemporalLagMonths, int):
            try:
                TemporalLagMonths = int(TemporalLagMonths)
            except ValueError:
                TemporalLagMonths = 0
        if not (TemporalLagMonths >= 0 and TemporalLagMonths <= 12):
            raise ValueError("Lag must be between 0 and 12 months (integer)")
        if not (Transform is None or isinstance(Transform, TransformAndAdjust)):
            raise ValueError("If a tranform is provided it must be an instance of the TransformAndAdjust type")

        self.Name = Name
        self._CubeResolution = CubeResolution
        self._CubeLevel = CubeLevel
        self._SpatialSummaryStat = SpatialSummaryType
        self._TemporalSummaryStat = TemporalSummaryType
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
        if self._TemporalLagMonths == 0:
            return RequiredOutputDate
        DataMonth = RequiredOutputDate - self._TemporalLagMonths * ONEMONTH
        return DataMonth

    def GenerateDataForDate(self, RequiredDate, lonLims=None, latLims=None, maskNoData=False):
        '''produces an array of data representing the content of the required term for this date

        This takes into account the temporal summary, anomaly, temporal lag, and transform as appropriate for this term.
        These are applied in the following order:
        1: apply lag to requested date, 2: read data, 3: apply anomaly if required, 4: apply offset, 5: apply transform
        The reading and anomaly calculation we apply here
        Date may be None if CubeLevel is synoptic, in which case the overall synoptic data will be read.

        '''
        if RequiredDate is None:
            cubeLevel = CubeLevels.STATIC # TODO what we gonna do here
        else:
            cubeLevel = self._CubeLevel
        dataDate = self.GetOffsetDate(RequiredDate)
        # The Cube object figures out what file to read based on the CubeLevel and the Date (or "None"), including if
        # it's a static variable. Read the "main" data for this term / date
        print("Output date is {0!s}; requesting cube object to read data for actual date {1!s}".format(RequiredDate, dataDate))
        dataArr, _gt, _proj, _ndv = self.DataCube.ReadDataForDate(cubeLevel, dataDate,
                                                                  maskNoData=maskNoData,
                                                                  lonLims=lonLims, latLims=latLims,
                                                                  useClosestAvailableYear=True)
        if _ndv is not None:
            ndMask = dataArr == _ndv
        else:
            ndMask = False
        if self._SpatialSummaryStat == CategoricalAggregationStats.PERCENTAGE:
            dataArr = dataArr / 100.0
        # some of the Pf terms are actually calculated in terms of difference between a monthly dynamic value and a
        # long-term average i.e. synoptic.
        isAnomaly = True
        if self._TemporalAnomalyType == TemporalAnomalyTypes.NONE:
            isAnomaly = False
        # If we need to calculate an anomaly, then use the same Cube to provide access to the synoptic data
        # from which this (presumably dynamic) term is differenced against. Use caching for the read of the synoptic
        # data so we don't have to re-read that file every time
        elif self._TemporalAnomalyType == TemporalAnomalyTypes.DIFF_SYNOPTIC_MONTHLY:
            secondaryArray, _, _, _ndSecondary = self.DataCube.ReadDataForDate(CubeLevels.SYNOPTIC_MONTHLY, dataDate,
                                                                    maskNoData=maskNoData, cacheThisRead = True,
                                                                    lonLims=lonLims, latLims=latLims)
            if _ndSecondary is not None:
                ndMask = ndMask + (secondaryArray == _ndSecondary)
            if self._SpatialSummaryStat == CategoricalAggregationStats.PERCENTAGE:
                dataArr = dataArr / 100.0
        elif self._TemporalAnomalyType == TemporalAnomalyTypes.DIFF_SYNOPTIC_ANNUAL:
            secondaryArray, _, _, _ndSecondary = self.DataCube.ReadDataForDate(CubeLevels.SYNOPTIC_OVERALL, None,
                                                                    maskNoData=maskNoData, cacheThisRead = True,
                                                                    lonLims=lonLims, latLims=latLims)
            if _ndSecondary is not None:
                ndMask = ndMask + (secondaryArray == _ndSecondary)
            if self._SpatialSummaryStat == CategoricalAggregationStats.PERCENTAGE:
                dataArr = dataArr / 100.0
        else:
            raise ValueError("Unknown temporal anomaly")

        # now build a string expression that represents what we need to do next with the array to apply anomaly and
        # offset; this is because we are using numexpr for faster calculation and it takes a string representation
        # of the python expression
        expr = "dataArr"
        if isAnomaly:
            expr = "(" + expr + " - secondaryArray)"
            outArr = ne.evaluate(expr)
        else:
            outArr = dataArr
        # now apply the transform, if there is one
        if self._Transformer is not None:
            outArr = self._Transformer.ApplyToData(outArr)
        if isinstance(ndMask, numpy.ndarray):
            outArr[ndMask] = _ndv
        return (outArr, _gt, _proj, _ndv)





