import numexpr as ne
import numpy as np
from enum import Enum

class TransformTypes(Enum):
    T1 = "Untransformed"
    T2 = "Normalize"
    T3 = "Reciprocal"
    T4 = "Log10"
    T5 = "Ln"
    T6 = "InverseHyperbolicSine"
    T7 = "Square"
    T8 = "SquareRoot"
    T9 = "CubeRoot"
    T10 = "BoxCox"
    T11 = "AbsNormal"


class TransformAndAdjust:
    def __init__(self, transformType, adjustmentOffset = 0, meanValue=None, stdValue=None,
                 thresholdValue=None, lambdaValue=None):
        if not isinstance(transformType, TransformTypes):
            transformType = TransformTypes(transformType)  # or raise valueerror

        if (transformType == TransformTypes.T2 or
            transformType == TransformTypes.T11):
            if meanValue is None or stdValue is None or meanValue == '' or stdValue == '':
                raise ValueError("Mean and std values must be provided for transform " + transformType.value)
            self._meanValue = float(meanValue)
            self._stdValue = float(stdValue)
        if transformType == TransformTypes.T10:
            if lambdaValue is None or lambdaValue == '':
                raise ValueError("Lambda value is required for BoxCox transform")
            self._lambdaValue = float(lambdaValue)
        if transformType == TransformTypes.T3:
            if thresholdValue is None or thresholdValue == '':
                raise ValueError("Threshold value is required for Reciprocal transform, or use string 'None'")
            else:
                try:
                    self._thresholdValue = float(thresholdValue)
                except:
                    self._thresholdValue = "None"
        # TODO more checking, that they're the same size etc
        self.TransformType = transformType
        self.AdjustmentOffset = float(adjustmentOffset)

    def log(self, message):
        print(message)

    def GetNumexprString(self, varname):
        pass

    def ApplyToData(self, dataArr):

        adj = self.AdjustmentOffset
        if self.TransformType == TransformTypes.T1:
            expr = "dataArr + adj"
        elif self.TransformType == TransformTypes.T2:
            meanValue = self._meanValue
            stdValue = self._stdValue
            expr = "((dataArr + adj) - meanValue) / stdValue"
        elif self.TransformType == TransformTypes.T3:
            thresh = self._thresholdValue
            if isinstance(thresh,float):
                if thresh <= 0:
                    raise ValueError("Threshold value must be positive (absolute values will be tested against it)")
                # the copious brackets seemed to be necessary to get numexpr to not whinge
                expr = "where((dataArr+adj)<thresh, (1.0/thresh), (1.0/(dataArr+adj)))"
                #expr = "where( (((dataArr+adj)<thresh) & ((dataArr+adj)>=0)), " \
                #       "(1.0/thresh), " \
                #       "where( ((abs(dataArr+adj)<thresh) & ((dataArr+adj)<0)), " \
                #       "(1.0/(-thresh)), " \
                #       "1.0/(dataArr+adj)))"
            else:
                expr = "1.0 / (dataArr + adj)"
        elif self.TransformType == TransformTypes.T4:
            expr = "log10(where((dataArr + adj)<=0.00001,0.00001,(dataArr + adj)))"
        elif self.TransformType == TransformTypes.T5:
            expr = "log(where((dataArr + adj)<=0.00001,0.00001,(dataArr + adj)))"
        elif self.TransformType == TransformTypes.T6:
            expr = "log(where(((dataArr + adj) + sqrt((dataArr + adj) ** 2 + 1))<=0.00001 " +\
                   ",0.00001" +\
                   ",((dataArr + adj) + sqrt((dataArr + adj) ** 2 + 1))))"
        elif self.TransformType == TransformTypes.T7:
            expr = "(dataArr + adj) ** 2"
        elif self.TransformType == TransformTypes.T8:
            expr = "where((dataArr + adj)<0, 0, sqrt(dataArr + adj))"
        elif self.TransformType == TransformTypes.T9:
            expr = "where((dataArr + adj)<0, 0, (dataArr + adj) ** (1.0/3))"
        elif self.TransformType == TransformTypes.T10:
            lambdaValue = self._lambdaValue or None
            expr = "where((dataArr + adj)<=0.00001, 0.00001 ** lambdaValue, (dataArr + adj) ** lambdaValue)"
        elif self.TransformType == TransformTypes.T11:
            meanValue = self._meanValue
            stdValue = self._stdValue
            expr = "abs(((dataArr + adj) - meanValue) / stdValue)"
        else:
            raise ValueError()
        self.log("Applying expression " + expr)
        return ne.evaluate(expr)
