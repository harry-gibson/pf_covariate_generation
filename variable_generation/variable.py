
from term import CovariateVariableTerm
from transforms import  TransformTypes, TransformAndAdjust

class MalariaCovariate:

    def __init__(self, Term1, Term2):
        assert isinstance(Term1, CovariateVariableTerm)
        assert isinstance(Term2, CovariateVariableTerm)
        # todo define proper type for transforms, and check for it
        self.Term1 = Term1
        self.Term2 = Term2


    def ProduceMonthData(self, RequiredMonth, lonLims=None, latLims=None):
        term1Data, _gt, _proj, _ndv = self.Term1.GenerateDataForDate(RequiredMonth,
                                                                     lonLims=lonLims, latLims=latLims,
                                                                     maskNoData=False)
        term2Data, _gt2, _proj2, _ndv2 = self.Term2.GenerateDataForDate(RequiredMonth,
                                                                        lonLims=lonLims, latLims=latLims,
                                                                        maskNoData=False)

        # todo check extent of the two variables and read them into either the union or intersection of the extents
        # e.g. http://sciience.tumblr.com/post/101722591382/finding-the-georeferenced-intersection-between-two

        # all variables are the product of two transformed terms, i.e. just a straight multiplication of them
        ndMask = (term1Data == _ndv) + (term2Data == _ndv2)
        res = term1Data * term2Data

        res[ndMask] = _ndv
        if ((_gt != _gt2) or (_proj != _proj2)):
            Warning("geotransform or proj seem to be different")
        return (res, _gt, _proj, _ndv)




