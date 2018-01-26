import numexpr as ne
import numpy as np
def t1_untransformed(dataArr):
    return arr
def t2_normalize(dataArr, meanArr, stdArr):
    expr= "(dataArr - meanArr) / stdArr"
    return ne.evaluate(expr)
def t3_reciprocal(dataArr):
    expr = "1.0 / dataArr"
    return ne.evaluate(expr)
def t4_log10(dataArr):
    expr = "log10(dataArr)"
    return ne.evaluate(expr)
def t5_ln(dataArr):
    expr = "log(dataArr)"
    return ne.evaluate(expr)
def t6_ihs(dataArr):
    expr = "log(dataArr + sqrt(dataArr ** 2 + 1))"
    return ne.evaluate(expr)
def t7_square(dataArr):
    expr = "dataArr ** 2"
    return ne.evaluate(expr)
def t8_sqrt(dataArr):
    expr = "sqrt(dataArr)"
    return ne.evaluate(dataArr)
def t9_cubrt(dataArr):
    expr = "dataArr ** (1.0/3)"
    return ne.evaluate(dataArr)
def t10_boxcox(dataArr):
    return whatthefuck
def t11_absnormal(dataArr, meanArr, stdArr):
    expr = "(dataArr / meanArr) / stdArr"
    return ne.evaluate(expr)