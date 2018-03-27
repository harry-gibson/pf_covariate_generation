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
    def __init__(self, transformType, adjustmentOffset = 0, meanValue=None, stdValue=None, lambdaValue=None):
        if not isinstance(transformType, TransformTypes):
            transformType = TransformTypes(transformType)  # or raise valueerror

        if (transformType == TransformTypes.T2 or
            transformType == TransformTypes.T11):
            if meanValue is None or stdValue is None:
                raise ValueError("Mean and std values must be provided for transform " + transformType.value)
            self._meanValue = meanValue
            self._stdValue = stdValue
        if transformType == TransformTypes.T10:
            if lambdaValue is None:
                raise ValueError("Lambda value is required for BoxCox transform")
            self._lambdaValue = lambdaValue
        # TODO more checking, that they're the same size etc
        self.TransformType = transformType
        self.AdjustmentOffset = adjustmentOffset

    def GetNumexprString(self, varname):
        pass

    def ApplyToData(self, dataArr):

        adjOffset = self.AdjustmentOffset
        if self.TransformType == TransformTypes.T1:
            expr = "dataArr + adjOffset"
        elif self.TransformType == TransformTypes.T2:
            meanValue = self._meanValue
            stdValue = self._stdValue
            expr = "((dataArr + adjOffset) - meanValue) / stdValue"
        elif self.TransformType == TransformTypes.T3:
            expr = "1.0 / (dataArr + adjOffset)"
        elif self.TransformType == TransformTypes.T4:
            expr = "log10(dataArr + adjOffset)"
        elif self.TransformType == TransformTypes.T5:
            expr = "log(dataArr + adjOffset)"
        elif self.TransformType == TransformTypes.T6:
            expr = "log((dataArr + adjOffset) + sqrt((dataArr + adjOffset) ** 2 + 1))"
        elif self.TransformType == TransformTypes.T7:
            expr = "(dataArr + adjOffset) ** 2"
        elif self.TransformType == TransformTypes.T8:
            expr = "sqrt((dataArr + adjOffset))"
        elif self.TransformType == TransformTypes.T9:
            expr = "(dataArr + adjOffset) ** (1.0/3)"
        elif self.TransformType == TransformTypes.T10:
            #return "whatthefuck" # TODO whatthefuck
            lambdaValue = self._lambdaValue or None
            expr = "(dataArr + adjOffset) ** lambdaValue"
        elif self.TransformType == TransformTypes.T11:
            meanValue = self._meanValue
            stdValue = self._stdValue
            expr = "((dataArr + adjOffset) - meanValue) / stdValue"
        else:
            raise ValueError()
        return ne.evaluate(expr)
