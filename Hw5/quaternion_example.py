"""Composition order and spin: numerical report with optional marked-prism view."""

import argparse
import math
from .geometry import Prism, world_mesh
from .rigid import RigidState, advance
from .spatial import from_axis_angle, compose, rotate, to_matrix, from_matrix, angular_distance


def results():
    """Fixed steps; no dependence on GUI timing."""
    x = from_axis_angle((1, 0, 0), math.pi/2)
    z = from_axis_angle((0, 0, 1), math.pi/2)
    orientations = [compose(z, x), compose(x, z)]
    shape = Prism(2, 1.4, .8, 1)
    state = RigidState(omega=(0, 0, 1.3))
    for _ in range(100):
        state, _ = advance(state, shape, .01, gravity=(0, 0, 0), ground=False)
    orientations.append(state.orientation)
    marker = (.7, .4, .5)  # same marked body vertex in all three panels
    residual = 0.0
    for q in orientations:
        matrix = to_matrix(q)
        for vector in (marker, (1, 0, 0), (0, 1, 0), (0, 0, 1)):
            by_matrix = tuple(sum(a*b for a, b in zip(row, vector)) for row in matrix)
            residual = max(residual, math.dist(rotate(q, vector), by_matrix))
        if angular_distance(q, from_matrix(matrix)) > 2e-12:
            raise RuntimeError('orientation round trip failed')
    if residual > 2e-12:
        raise RuntimeError('quaternion/matrix disagreement')
    return shape, orientations, marker, residual, state


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--headless', action='store_true', help='numerics only unless --snapshot is given')
    parser.add_argument('--show', action='store_true', help='show static comparison in a GUI window')
    parser.add_argument('--snapshot', help='save comparison PNG using Agg, no GUI')
    args = parser.parse_args(argv)
    if args.headless and args.show:
        parser.error('--headless and --show are incompatible')
    shape, orientations, marker, residual, state = results()
    labels = ('x then z (world axes)', 'z then x (world axes)', 'z spin: 1 s, 100 steps')
    for label, q in zip(labels, orientations):
        print(label, 'q=', tuple(round(x, 9) for x in q),
              'marked corner=', tuple(round(x, 9) for x in rotate(q, marker)))
    print(f'quaternion/matrix max vector residual: {residual:.3g} m')
    angle = 2*math.atan2(state.orientation[3], state.orientation[0])
    print(f'spin angle: {angle:.12f} rad; continuous: 1.300000000000 rad; '
          f'phase lag: {1.3-angle:.6g} rad; omega={state.omega}')
    print('rotation separation between orders:', f'{angular_distance(*orientations[:2]):.12f} rad')
    if not (args.show or args.snapshot):
        return 0
    import matplotlib
    if args.snapshot:
        matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    figure = plt.figure(figsize=(13, 4.5))
    for i, (label, q) in enumerate(zip(labels, orientations)):
        axes = figure.add_subplot(1, 3, i+1, projection='3d')
        axes.computed_zorder = False  # Keep the identifying mark visible through faces.
        faces = [[(x, z, y) for x, y, z in face] for face in world_mesh(shape, (0, 0, 0), q)]
        axes.add_collection3d(Poly3DCollection(faces, facecolor='#489bb2',
                                             edgecolor='#28505d', alpha=.45, zorder=1))
        for axis, color in zip(((1, 0, 0), (0, 1, 0), (0, 0, 1)), ('r', 'g', 'b')):
            x, y, z = rotate(q, axis)
            axes.plot((0, x), (0, z), (0, y), color=color, linewidth=2, zorder=2)
        x, y, z = rotate(q, marker)
        axes.scatter([x], [z], [y], color='red', marker='*', s=120, depthshade=False, zorder=3)
        axes.set(xlim=(-1.2, 1.2), ylim=(-1.2, 1.2), zlim=(-1.2, 1.2),
                 xticks=(-1, 0, 1), yticks=(-1, 0, 1), zticks=(-1, 0, 1),
                 xlabel='world x', ylabel='world z', zlabel='world y', title=label)
        axes.set_box_aspect((1, 1, 1))
    figure.suptitle('Same prism and marked corner | body axes: red x, green y, blue z')
    figure.tight_layout()
    if args.snapshot:
        figure.savefig(args.snapshot, dpi=140, bbox_inches='tight')
        plt.close(figure)
    else:
        plt.show()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
