
from term import FiveKCovariateVariableTerm


class MalariaCovariate:

    def __init__(self, Term1, Transform1, Term2, Transform2):
        assert isinstance(Term1, FiveKCovariateVariableTerm)
        assert isinstance(Term2, FiveKCovariateVariableTerm)
        # todo define proper type for transforms, and check for it
        self.Term1 = Term1
        self.Term2 = Term2
        self.Transform1 = Transform1
        self.Transform2 = Transform2

    def ProduceMonthData(self, RequiredMonth):
        term1Data = self.Term1.ReadDataForDate(RequiredMonth)
        # todo deal with transforms that need another array too
        # todo do in one step to save mem
        term1Data = self.Transform1(term1Data)
        term2Data = self.Term2.ReadDataForDate(RequiredMonth)
        term2Data = self.Transform2(RequiredMonth)

        # all variables are the product of two transformed terms, i.e. just a straight multiplication of them
        return term1Data * term2Data

