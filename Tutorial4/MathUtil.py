PI = 3.14159265
EPSILON = 1e-10

class operandLessThanZeroError(Exception):

    def __init__(self, message, operand = None):
        super().__init__(message)

        self.operand = operand

    def __str__(self):
        return f"operandLessThanZeroError: {self.operand if self.operand is not None else 'Op not provided'}"

    def __repr__(self):
        return f"operandLessThanZeroError: {self.operand if self.operand is not None else 'Op not provided'}"

def sqrtReal(x):
    """_summary_

    Args:
        x (_type_): _description_

    Raises:
        operandLessThanZeroError: _description_

    Returns:
        _type_: _description_
    """
    if x < 0:
        raise operandLessThanZeroError("Cannot compute real square root of a negative number.", operand = x)
    initial_guess = x / 2
    guess = initial_guess
    while True:
        next_guess = (guess + x / guess) / 2
        if abs(next_guess - guess) < EPSILON:
            return next_guess
        guess = next_guess

if __name__ == "__main__":
    sqrt_of_4 = sqrtReal(4)
    print(f"The square root of 4 is: {sqrt_of_4}")
    try:
        sqrt_of_n9 = sqrtReal(-9)  
    except operandLessThanZeroError as e:
        print(e)