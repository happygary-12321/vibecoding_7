"""Three independent rotating solids: headless numerics or Matplotlib animation."""

import argparse
import math
from .geometry import Prism, Sphere, Cylinder, ground_support, world_mesh
from .rigid import RigidState, advance
from .spatial import add, rotate


def simulate():
    """Deterministic 3 s scene at 240 Hz, sampled at 30 Hz; no body collisions."""
    shapes = (Prism(2, 1.2, .7, .9), Sphere(1.5, .55), Cylinder(2.5, .45, 1.4))
    states = [RigidState((-3, 2.5, 0), (.1, 0, 0), omega=(1, .7, 1.3)),
              RigidState((0, 3.2, 0), (.1, 0, 0), omega=(1.5, 1, .5)),
              RigidState((3, 2.8, 0), (-.1, 0, 0),
                         (math.cos(.4), math.sin(.4), 0, 0), (1.2, .7, 1))]
    frames = [tuple(states)]
    impacts = [0, 0, 0]
    for n in range(720):
        for i, shape in enumerate(shapes):
            states[i], contact = advance(states[i], shape, 1/240, restitution=.65)
            if contact is not None and contact.impulse > 0:
                impacts[i] += 1
            clearance = ground_support(shape, states[i].position, states[i].orientation)[1]
            if clearance < -1e-10:
                raise RuntimeError("endpoint ground projection failed")
        if (n+1) % 8 == 0:
            frames.append(tuple(states))
    if not all(impacts):
        raise RuntimeError("showcase must exercise impact for every shape")
    return shapes, frames, impacts


def draw_scene(shapes, states, axes):
    """Map world (x,y,z) to plot (x,z,y), keeping world y visibly up."""
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    axes.clear()
    axes.add_collection3d(Poly3DCollection(
        [[(-5, -2, 0), (5, -2, 0), (5, 2, 0), (-5, 2, 0)]],
        facecolor='#e7e9ee', edgecolor='#9299aa', alpha=.4))
    for shape, state, color in zip(shapes, states, ('#de7b33', '#2d91b1', '#8a65b8')):
        faces = [[(x, z, y) for x, y, z in face]
                 for face in world_mesh(shape, state.position, state.orientation, 16)]
        axes.add_collection3d(Poly3DCollection(faces, facecolor=color,
                                             edgecolor=color, linewidth=.2, alpha=.7))
        # All three body axes make the sphere's otherwise invisible spin observable.
        length = .8
        for axis, marker_color in zip(((length, 0, 0), (0, length, 0), (0, 0, length)),
                                      ('#b52b26', '#1c7c35', '#2448bb')):
            end = add(state.position, rotate(state.orientation, axis))
            p = state.position
            axes.plot((p[0], end[0]), (p[2], end[2]), (p[1], end[1]), color=marker_color, linewidth=2)
    axes.set(xlim=(-5, 5), ylim=(-2, 2), zlim=(0, 4.5),
             xlabel='world x (m)', ylabel='world z (m)', zlabel='world y (m)',
             title=f'Independent solids | t={states[0].time:.2f} s | no body-body collisions')
    axes.set_box_aspect((10, 4, 4.5))
    axes.view_init(elev=20, azim=-65)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--headless', action='store_true', help='numerical verification, no plotting imports')
    parser.add_argument('--snapshot', help='optional PNG at t=1 s using Agg, no window')
    args = parser.parse_args(argv)
    shapes, frames, impacts = simulate()
    for shape, state, count in zip(shapes, frames[-1], impacts):
        print(type(shape).__name__, 'steps=', state.step_count, 'time=', round(state.time, 9),
              'position=', tuple(round(x, 6) for x in state.position),
              'omega=', tuple(round(x, 6) for x in state.omega), 'impacts=', count)
    if args.headless and not args.snapshot:
        return 0
    import matplotlib
    if args.snapshot:
        matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    figure = plt.figure(figsize=(11, 6))
    axes = figure.add_subplot(111, projection='3d')
    if args.snapshot:
        draw_scene(shapes, frames[30], axes)
        figure.savefig(args.snapshot, dpi=140, bbox_inches='tight')
        plt.close(figure)
    else:
        from matplotlib.animation import FuncAnimation
        animation = FuncAnimation(figure, lambda i: draw_scene(shapes, frames[i], axes),
                                  frames=len(frames), interval=1000/30, repeat=True)
        plt.show()
        # Keep the animation alive until the window closes.
        del animation
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
