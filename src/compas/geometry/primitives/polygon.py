from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import math

from compas.geometry.basic import cross_vectors

from compas.geometry.average import centroid_points
from compas.geometry.average import centroid_polygon

from compas.geometry.size import area_polygon

from compas.geometry.queries import is_coplanar
from compas.geometry.queries import is_polygon_convex

from compas.geometry.primitives import Primitive
from compas.geometry.primitives import Point
from compas.geometry.primitives import Vector
from compas.geometry.primitives import Line

from compas.geometry import transform_points

__all__ = ['Polygon']


class Polygon(Primitive):
    """An object representing an ordered collection of points in space connected
    by straight line segments forming a closed boundary around the interior space.

    A polygon has a closed boundary that separates its interior from the
    exterior. The boundary does not intersect itself, and is described by an
    ordered set of of points.

    Parameters
    ----------
    points : list of point
        An ordered list of points.

    Examples
    --------
    >>> polygon = Polygon([[0,0,0], [1,0,0], [1,1,0], [0,1,0]])
    >>> polygon.centroid
    Point(0.500, 0.500, 0.000)
    >>> polygon.area
    1.0

    Notes
    -----
    All ``Polygon`` objects are considered closed. Therefore the first and
    last element in the list of points are not the same. The existence of the
    closing edge is implied.

    Polygons are not necessarily planar by construction; they can be warped.

    """

    def __init__(self, points):
        self._points = []
        self._lines = []
        self.points = points

    # ==========================================================================
    # factory
    # ==========================================================================

    @classmethod
    def from_data(cls, data):
        """Construct a polygon from its data representation.

        Parameters
        ----------
        data : :obj:`dict`
            The data dictionary.

        Returns
        -------
        Polygon
            The constructed polygon.

        Examples
        --------
        >>>

        """
        return cls(data['points'])

    @classmethod
    def from_sides_and_radius(cls, sides, radius):
        """Construct a regular polygon from a number of sides and a radius.
        The resulting polygon is equilateral and equiangular.
        Its winding is clockwise and lies on the XY-plane.

        Parameters
        ----------
        sides : int
            The number of sides.
        radius : float
            The radius of the polygon's circumscribed circle.

        Returns
        -------
        Polygon
            The constructed polygon.

        Examples
        --------
        >>> from compas.geometry import normal_polygon
        >>> pentagon = Polygon.from_sides_and_radius(5, 1.0)
        >>> len(pentagon.points) == 5
        True
        >>> normal_polygon(pentagon)
        (0.0, 0.0, -1.0)
        >>> len({round(line.length, 6) for line in pentagon.lines}) == 1
        True
        """
        if sides < 3:
            raise ValueError("Supplied number of sides must be at least 3!")

        side = math.pi * 2 / sides

        points = []
        for i in range(sides):
            point = [math.sin(side * i) * radius,
                     math.cos(side * i) * radius,
                     0.]
            points.append(point)

        return cls(points)

    # ==========================================================================
    # descriptors
    # ==========================================================================

    @property
    def data(self):
        """Returns the data dictionary that represents the polygon.

        Returns
        -------
        dict
            The polygon data.

        """
        return {'points': [list(point) for point in self.points]}

    @data.setter
    def data(self, data):
        self.points = data['points']

    @property
    def points(self):
        """list of Point: The points of the polygon."""
        return self._points

    @points.setter
    def points(self, points):
        if points[-1] == points[0]:
            del points[-1]
        self._points = [Point(*xyz) for xyz in points]
        self._lines = [Line(self.points[i], self.points[i + 1]) for i in range(-1, len(points) - 1)]

    @property
    def lines(self):
        """list of Line: The lines of the polyline."""
        return self._lines

    @property
    def length(self):
        """float: The length of the boundary."""
        return sum([line.length for line in self.lines])

    @property
    def centroid(self):
        """int: The centroid of the polygon."""
        return Point(* centroid_points(self.points))

    @property
    def center(self):
        """Point: The center (of mass) of the polygon."""
        return Point(* centroid_polygon(self.points))

    @property
    def normal(self):
        """Vector: The (average) normal of the polygon."""
        o = self.center
        points = self.points
        a2 = 0
        normals = []
        for i in range(-1, len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]
            u = [p1[_] - o[_] for _ in range(3)]
            v = [p2[_] - o[_] for _ in range(3)]
            w = cross_vectors(u, v)
            a2 += sum(w[_] ** 2 for _ in range(3)) ** 0.5
            normals.append(w)
        n = [sum(axis) / a2 for axis in zip(*normals)]
        n = Vector(* n)
        return n

    @property
    def area(self):
        """float: The area of the polygon."""
        return area_polygon(self.points)

    # ==========================================================================
    # representation
    # ==========================================================================

    def __repr__(self):
        return "Polygon({})".format(", ".join(["{}".format(point) for point in self.points]))

    def __len__(self):
        return len(self.points)

    # ==========================================================================
    # access
    # ==========================================================================

    def __getitem__(self, key):
        return self.points[key]

    def __setitem__(self, key, value):
        self.points[key] = value

    def __iter__(self):
        return iter(self.points)

    # ==========================================================================
    # comparison
    # ==========================================================================

    def __eq__(self, other):
        raise NotImplementedError

    # ==========================================================================
    # operators
    # ==========================================================================

    # ==========================================================================
    # inplace operators
    # ==========================================================================

    # ==========================================================================
    # helpers
    # ==========================================================================

    def copy(self):
        """Make a copy of this ``Polygon``.

        Returns
        -------
        Polygon
            The copy.

        """
        cls = type(self)
        return cls([point.copy() for point in self.points])

    # ==========================================================================
    # methods
    # ==========================================================================

    def is_convex(self):
        """Determine if the polygon is convex.

        Returns
        -------
        bool
            True if the polygon is convex.
            False otherwise.

        """
        return is_polygon_convex(self.points)

    def is_planar(self):
        """Determine if the polygon is planar.

        Returns
        -------
        bool
            True if all points of the polygon lie in one plane.
            False otherwise.

        """
        return is_coplanar(self.points)

    # ==========================================================================
    # transformations
    # ==========================================================================

    def transform(self, matrix):
        """Transform this ``Polygon`` using a given transformation matrix.

        Parameters
        ----------
        matrix : list of list
            The transformation matrix.

        """
        for index, point in enumerate(transform_points(self.points, matrix)):
            self.points[index].x = point[0]
            self.points[index].y = point[1]
            self.points[index].z = point[2]

    def transformed(self, matrix):
        """Return a transformed copy of this ``Polygon`` using a given transformation matrix.

        Parameters
        ----------
        matrix : list of list
            The transformation matrix.

        Returns
        -------
        Polygon
            The transformed copy.

        """
        polygon = self.copy()
        polygon.transform(matrix)
        return polygon


# ==============================================================================
# Main
# ==============================================================================

if __name__ == '__main__':

    import doctest

    print(Polygon([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 1.0, 0.0], [0.0, 1.0, 0.0]]))

    doctest.testmod(globs=globals())
