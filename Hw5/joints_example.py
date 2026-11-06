"""Fixed dynamic pair, revolute pendulum and driven prismatic slider."""

import argparse
import math
from .geometry import Prism, Sphere, Cylinder, world_mesh
from .rigid import RigidState
from .spatial import from_axis_angle, rotate, add, scale
from .joints import make_joint, advance_system, Load, joint_coordinates


def simulate():
    """Three independent demonstrations, each with fully dynamic finite bodies."""
    fixed = (RigidState((-.6, 1, 0)), RigidState((.6, 1, 0)))
    theta, length = .5, .8
    pendulum = (RigidState((length*math.sin(theta), -length*math.cos(theta), 0),
                          orientation=from_axis_angle((0, 0, 1), theta)),)
    axis = (1, .3, .2)
    size = math.sqrt(sum(x*x for x in axis))
    axis = tuple(x/size for x in axis)
    slider = (RigidState(orientation=from_axis_angle((-axis[1], axis[0], 0), math.acos(axis[2]))),)
    scenes = [
        dict(name='fixed', states=fixed, shapes=(Prism(2, .8, .6, .5), Sphere(3, .35)),
             joint=make_joint('fixed', fixed, 0, 1, (0, 1, 0)), gravity=(0, 0, 0),
             loads=(Load(force=(.4, .1, 0), torque=(0, 0, .6), force_point=(-.5, 1.3, 0)), Load())),
        dict(name='revolute', states=pendulum, shapes=(Prism(2, .4, 1.4, .4),),
             joint=make_joint('revolute', pendulum, None, 0), gravity=(0, -9.81, 0), loads=(Load(),)),
        dict(name='prismatic', states=slider, shapes=(Cylinder(2, .25, .8),),
             joint=make_joint('prismatic', slider, None, 0, axis=axis), gravity=(0, 0, 0),
             loads=(Load(force=scale(axis, 2)),)),
    ]
    for scene in scenes:
        scene['frames'] = [scene['states']]
        maxima = [0.0]*4
        for n in range(300):
            scene['states'], report = advance_system(scene['states'], scene['shapes'], (scene['joint'],),
                                                      .005, loads=scene['loads'], gravity=scene['gravity'])
            r = report.residuals
            maxima = [max(a, b) for a, b in zip(maxima, (r.position_m, r.orientation_rad,
                                                       r.linear_velocity_m_s, r.angular_velocity_rad_s))]
            if (n+1) % 10 == 0:
                scene['frames'].append(scene['states'])
        scene['max_residuals'] = tuple(maxima)
    return scenes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--snapshot', help='optional PNG, uses Agg')
    parser.add_argument('--show', action='store_true', help='optional static comparison window')
    args = parser.parse_args(argv)
    if args.headless and args.show:
        parser.error('--headless and --show are incompatible')
    scenes = simulate()
    for scene in scenes:
        print(scene['name'], 't=1.5 s, steps=300, coordinate=', f"{joint_coordinates(scene['states'], scene['joint']):.9f}")
        print('  max residuals (m,rad,m/s,rad/s)=', scene['max_residuals'])
        for i, s in enumerate(scene['states']):
            print('  body', i, 'position=', tuple(round(x, 6) for x in s.position),
                  'velocity=', tuple(round(x, 6) for x in s.velocity),
                  'omega_body=', tuple(round(x, 6) for x in s.omega))
    if not (args.snapshot or args.show):
        return 0
    import matplotlib
    if args.snapshot:
        matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection
    figure = plt.figure(figsize=(14, 5))
    for k, scene in enumerate(scenes):
        axes = figure.add_subplot(1, 3, k+1, projection='3d')
        axes.computed_zorder = False
        for i, (shape, s) in enumerate(zip(scene['shapes'], scene['states'])):
            initial = scene['frames'][0][i]
            ghost = [[(x, z, y) for x, y, z in face]
                     for face in world_mesh(shape, initial.position, initial.orientation, 16)]
            edges = [(face[i], face[(i+1) % len(face)]) for face in ghost for i in range(len(face))]
            axes.add_collection3d(Line3DCollection(edges,
                                                  colors='#aaaabb', linewidths=.5, alpha=.4, zorder=1))
            faces = [[(x, z, y) for x, y, z in face] for face in world_mesh(shape, s.position, s.orientation, 16)]
            axes.add_collection3d(Poly3DCollection(faces, facecolor=('#478ea7', '#db8a3b')[i % 2],
                                                 edgecolor='gray', alpha=.65, zorder=2))
            points = [frame[i].position for frame in scene['frames']]
            axes.plot([p[0] for p in points], [p[2] for p in points], [p[1] for p in points],
                      color='gray', linestyle='--', zorder=1)
            mark = add(s.position, rotate(s.orientation, (.3, 0, 0)))
            axes.plot((s.position[0], mark[0]), (s.position[2], mark[2]), (s.position[1], mark[1]), color='red', zorder=3)
        joint = scene['joint']
        if joint.a is None:
            anchor, axis = joint.anchor_a, joint.axis_a
        else:
            a = scene['states'][joint.a]
            anchor = add(a.position, rotate(a.orientation, joint.anchor_a))
            axis = rotate(a.orientation, joint.axis_a)
        end = add(anchor, scale(axis, .6 if scene['name'] != 'prismatic' else 2))
        axes.scatter([anchor[0]], [anchor[2]], [anchor[1]], color='black', s=45, zorder=5)
        if scene['name'] == 'fixed':
            a, b = (s.position for s in scene['states'])
            axes.plot((a[0], b[0]), (a[2], b[2]), (a[1], b[1]), color='black', zorder=3)
        else:
            axes.plot((anchor[0], end[0]), (anchor[2], end[2]), (anchor[1], end[1]), color='black', linewidth=2, zorder=4)
        if scene['name'] == 'revolute':
            center = scene['states'][0].position
            axes.plot((anchor[0], center[0]), (anchor[2], center[2]), (anchor[1], center[1]), color='black')
        axes.set(title=scene['name'], xlabel='world x (m)', ylabel='world z (m)', zlabel='',
                 xlim=(-1.5, 2), ylim=(-1, 1), zlim=(-1.5, 2),
                 xticks=(-1, 0, 1, 2), yticks=(-1, 0, 1), zticks=(-1, 0, 1, 2))
        axes.set_box_aspect((3.5, 2, 3.5))
        axes.text2D(.92, .55, 'world y (m)', rotation=90, fontsize=9, transform=axes.transAxes)
    figure.suptitle('Dynamic joints at t=1.5 s | black: anchors, weld or permitted axes | gray: initial poses / COM trails')
    figure.subplots_adjust(left=.02, right=.92, bottom=.12, top=.87, wspace=.16)
    if args.snapshot:
        figure.savefig(args.snapshot, dpi=140, bbox_inches='tight')
        plt.close(figure)
    else:
        plt.show()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
