from MathUtil import EPSILON 
from MathUtil import sqrtReal

def test_result(a, b, c, x1, x2):
    return abs(a*x1**2 + b*x1 + c) < EPSILON and abs(a*x2**2 + b*x2 + c) < EPSILON

def solveQuadratic(a, b, c):
    pass

if __name__ == "__main__":
    while True:
        pass