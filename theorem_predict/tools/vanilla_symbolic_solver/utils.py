import math
import sys
from math import sqrt, sin, pi


def isNumber(number):
    try:
        float(number)
        return True
    except:
        return False
    
def hasNumber(lst):
    for number in lst:
        try:
            float(number)
            return True
        except:
            pass
    return False

# Note: We should calculate the value explicitly, so use math.xxx not sympy.xxx

def heron_triangle_formula(a,b,c):
    s = (a+b+c)/2
    return sqrt(s*(s-a)*(s-b)*(s-c))

def angle_area_formula(a,b, angle):
    return 0.5 * a * b * sin(pi / 180.0 * angle)

def cos_law_length():
    pass

def cos_law_angle():
    pass

def sin_law_length():
    pass

def sin_law_angle():
    pass

if __name__ == '__main__':
    area = heron_triangle_formula(3,4,5)
    assert area == 6.0
    area = angle_area_formula(3,4,90)
    assert area == 6.0


