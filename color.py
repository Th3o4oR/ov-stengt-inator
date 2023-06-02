class Color:
    def __init__(self, r: float, g: float, b: float, name: str):
        self.red:   float = r
        self.green: float = g
        self.blue:  float = b
        self.name:  str   = name

    def __add__(self, rhs):
        color: Color = Color(
            self.red + rhs.red,
            self.green + rhs.green,
            self.blue + rhs.blue,
            self.name
        )

        return color

    def __sub__(self, rhs):
        color: Color = Color(
            self.red - rhs.red,
            self.green - rhs.green,
            self.blue - rhs.blue,
            self.name
        )

        return color

    def __mul__(self, rhs: float):
        color: Color = Color(
            self.red * rhs,
            self.green * rhs,
            self.blue * rhs,
            self.name
        )

        return color   

    def __rmul__(self, lhs):
        return self.__mul__(lhs)

    def __truediv__(self, rhs: float):
        color: Color = Color(
            self.red / rhs,
            self.green / rhs,
            self.blue / rhs,
            self.name
        )

        return color

    def __rtruediv__(self, lhs):
        return self.__truediv__(lhs)
