"""Free-flight damping comparison: fixed steps, numerical report, optional plot."""

import argparse
import math
from .geometry import Sphere
from .rigid import RigidState, advance
from .spatial import rotate


def histories():
    """Same marked sphere: m=5 kg, R=1 m, literal I=(2,2,2) kg m^2."""
    shape = Sphere(5, 1)
    initial = RigidState(velocity=(1, .4, -.3), omega=(0, 0, 2))
    series = {}
    for name, c, cw in (('undamped', 0, 0), ('damped', 2, 1)):
        s = initial
        records, angle, previous = [], 0.0, 0.0
        for n in range(401):
            if n:
                s, _ = advance(s, shape, .01, gravity=(0, 0, 0), ground=False,
                               linear_damping=c, angular_damping=cw)
            marker = rotate(s.orientation, (1, 0, 0))
            phase = math.atan2(marker[1], marker[0])
            angle += math.atan2(math.sin(phase-previous), math.cos(phase-previous))
            previous = phase
            # Independent demo calculation, not a production energy oracle/helper.
            energy = 2.5*sum(v*v for v in s.velocity)+sum(w*w for w in s.omega)
            records.append(dict(time=s.time, state=s, speed=math.hypot(*s.velocity),
                                angular_speed=math.hypot(*s.omega), energy=energy,
                                angle=angle, marker=marker))
        series[name] = records
    if not all(b['energy'] < a['energy'] for a, b in zip(series['damped'], series['damped'][1:])):
        raise RuntimeError('unforced damped sphere must lose kinetic energy')
    return series


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--headless', action='store_true', help='numerical output without GUI')
    parser.add_argument('--snapshot', help='optional PNG using Agg')
    parser.add_argument('--show', action='store_true', help='optional GUI plot')
    args = parser.parse_args(argv)
    if args.headless and args.show:
        parser.error('--headless and --show are incompatible')
    series = histories()
    print('Free flight: gravity=0, ground=False, no external loads; m=5, I=(2,2,2)')
    print('damped coefficients: c=2 N*s/m, c_omega=1 N*m*s/rad; h=.01 s')
    print('case t_s speed_m_s angular_speed_rad_s energy_J marked_axis_angle_rad')
    for name, records in series.items():
        for row in records[::100]:
            print(name, *(f"{row[key]:.9f}" for key in ('time', 'speed', 'angular_speed', 'energy', 'angle')))
    if not (args.snapshot or args.show):
        return 0
    import matplotlib
    if args.snapshot:
        matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    figure, axes = plt.subplots(2, 3, figsize=(13, 7))
    plots = (('speed', 'Speed (m/s)'), ('angular_speed', 'Angular speed (rad/s)'),
             ('energy', 'Kinetic energy (J)'), ('distance', 'COM distance traveled (m)'),
             ('angle', 'Unwrapped marked-axis angle (rad)'))
    for axis, (key, label) in zip(axes.flat, plots):
        for name, records in series.items():
            values = [math.hypot(*r['state'].position) if key == 'distance' else r[key] for r in records]
            axis.plot([r['time'] for r in records], values, label=name)
        axis.set(xlabel='time (s)', ylabel=label)
        axis.grid(alpha=.3)
        axis.legend()
    # Final surface mark and body-x direction: same sphere, different spin histories.
    axis = axes[1, 2]
    circle = [2*math.pi*i/128 for i in range(129)]
    axis.plot([math.cos(t) for t in circle], [math.sin(t) for t in circle], color='gray')
    for name, records in series.items():
        x, y, _ = records[-1]['marker']
        axis.plot([0, x], [0, y], label=name, linewidth=2)
        axis.scatter([x], [y], marker='*', s=130)
    axis.set(xlabel='world x', ylabel='world y', title='Sphere surface mark at t=4 s',
             xlim=(-1.2, 1.2), ylim=(-1.2, 1.2), aspect='equal')
    axis.legend()
    figure.suptitle('Identical marked spheres | zero vs viscous damping | unforced free flight')
    figure.tight_layout()
    if args.snapshot:
        figure.savefig(args.snapshot, dpi=140, bbox_inches='tight')
        plt.close(figure)
    else:
        plt.show()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
