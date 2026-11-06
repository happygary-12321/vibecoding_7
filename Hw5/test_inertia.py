"""Independent interior volume quadrature; no production sample generators."""

import math
import unittest
from Hw5.geometry import Prism, Sphere, Cylinder


def samples(kind, n):
    """Fixed fixtures, points strictly inside each solid, mass weights = rho*dV.

    Prism: m=12, sides 2,4,6. Sphere: m=5,R=2. Cylinder: m=6,R=2,L=6.
    Exact shell/annulus volume weights, midpoint radii/angles/heights.
    """
    if kind == 'prism':
        for i in range(n):
            for j in range(n):
                for k in range(n):
                    yield ((-1+2*(i+.5)/n, -2+4*(j+.5)/n, -3+6*(k+.5)/n), 12/n**3)
    else:
        for i in range(n):
            low, high = 2*i/n, 2*(i+1)/n
            r = (low+high)/2
            for j in range(n):
                for k in range(2*n):
                    phi = 2*math.pi*(k+.5)/(2*n)
                    if kind == 'sphere':
                        mu = -1+2*(j+.5)/n
                        point = (r*math.sqrt(1-mu*mu)*math.cos(phi),
                                 r*math.sqrt(1-mu*mu)*math.sin(phi), r*mu)
                        weight = 5*(high**3-low**3)/8/(2*n*n)
                    else:
                        point = (r*math.cos(phi), r*math.sin(phi), -3+6*(j+.5)/n)
                        weight = 6*(high**2-low**2)/4/(2*n*n)
                    yield point, weight


def integrate(kind, n, origin=(0, 0, 0)):
    tensor = [[0.0]*3 for _ in range(3)]
    mass, first = 0.0, [0.0]*3
    for p, weight in samples(kind, n):
        if kind == 'prism':
            assert abs(p[0]) < 1 and abs(p[1]) < 2 and abs(p[2]) < 3
        elif kind == 'sphere':
            assert sum(x*x for x in p) < 4
        else:
            assert p[0]**2+p[1]**2 < 4 and abs(p[2]) < 3
        mass += weight
        for i in range(3):
            first[i] += weight*p[i]
        r = [p[i]-origin[i] for i in range(3)]
        r2 = sum(x*x for x in r)
        for i in range(3):
            for j in range(3):
                tensor[i][j] += weight*((r2 if i == j else 0)-r[i]*r[j])
    return tensor, mass, first


class InertiaSamplingTests(unittest.TestCase):
    fixtures = (('prism', Prism(12, 2, 4, 6), (52, 40, 20)),
                ('sphere', Sphere(5, 2), (8, 8, 8)),
                ('cylinder', Cylinder(6, 2, 6), (24, 24, 12)))

    def test_interior_quadrature_refinement(self):
        for kind, shape, literal in self.fixtures:
            errors = []
            for n in (8, 16):
                tensor, mass, first = integrate(kind, n)
                self.assertAlmostEqual(mass, shape.mass, delta=1e-10)
                for value in first:
                    self.assertAlmostEqual(value, 0, delta=1e-10)
                for i in range(3):
                    self.assertAlmostEqual(shape.inertia[i], literal[i], delta=1e-12)
                    for j in range(3):
                        if i != j:
                            self.assertAlmostEqual(tensor[i][j], 0, delta=1e-10)
                error = max(abs(tensor[i][i]-shape.inertia[i])/literal[i] for i in range(3))
                self.assertLess(error, 2/n**2)  # midpoint quadrature, not dynamics error
                errors.append(error)
            self.assertGreater(errors[0], 1e-5)
            self.assertGreater(errors[1]/errors[0], .20)
            self.assertLess(errors[1]/errors[0], .30)
            print(kind, 'quadrature relative error n=8,16:', errors)

    def test_parallel_axis_offset_tensor(self):
        # MIT L26 PDF p7. O is displaced d from COM; tensor off-diagonals -m*d_i*d_j.
        d = (.3, -.4, .5)
        for kind, shape, literal in self.fixtures:
            for n in (8, 16):
                centered, _, _ = integrate(kind, n)
                offset, _, _ = integrate(kind, n, d)
                for i in range(3):
                    for j in range(3):
                        shift = shape.mass*((sum(x*x for x in d) if i == j else 0)-d[i]*d[j])
                        # Quadrature errors cancel here; symmetry gives exact first moment.
                        self.assertAlmostEqual(offset[i][j]-centered[i][j], shift, delta=1e-10)
                        # Also connect sampled offset tensor to production COM inertia.
                        expected = shape.inertia_tensor[i][j]+shift
                        tolerance = 2*max(literal)/n**2 if i == j else 1e-10
                        self.assertAlmostEqual(offset[i][j], expected, delta=tolerance)


if __name__ == '__main__':
    unittest.main(verbosity=2)
