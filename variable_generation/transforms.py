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
    def __init__(self, transformType, adjustmentOffset = 0):
        assert isinstance(transformType, TransformTypes)
        self.TransformType = transformType
        self.AdjustmentOffset = adjustmentOffset

    def Apply(self, dataArr, meanArr = None, stdArr = None):
        if (self.TransformType == TransformTypes.T2 or
            self.TransformType == TransformTypes.T11):
            assert (meanArr is not None) and (stdArr is not None)
            # TODO more checking, that they're the same size etc
        adjOffset = self.AdjustmentOffset
        if self.TransformType == TransformTypes.T1:
            expr = "dataArr + adjOffset"
        elif self.TransformType == TransformTypes.T2:
            expr = "((dataArr + adjOffset) - meanArr) / stdArr"
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
            return "whatthefuck" # TODO whatthefuck
        elif self.TransformType == TransformTypes.T11:
            expr = "((dataArr + adjOffset) - meanArr) / stdArr"
        else:
            raise ValueError()
        return ne.evaluate(expr)
