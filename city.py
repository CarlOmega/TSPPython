import math
class City:
    """A class to store the city details."""
    def __init__(self, id, x, y):
        self.ID = id
        self.X = x
        self.Y = y

    def dist(self, other):
        xd = self.X - other.X;
        yd = self.Y - other.Y;
        dij = math.sqrt(xd*xd + yd*yd);
        return dij

    def print_all(self):
        print(self.ID, self.X, self.Y)
