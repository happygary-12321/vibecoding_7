"""Fixed-step serial falling-solids example. Run from the repository root."""
import argparse
from collections import Counter
from dataclasses import asdict
import json
import math
from pathlib import Path
import time
from .model import Options
from .scene import make_scene
from .world import simulate, kinetic_energy


def summary(result):
    bodies, reports = result.world.bodies, result.reports
    dynamic = [b for b in bodies if not b.static]
    depths = sorted(r.penetration_after for r in reports)
    impacts = [i for r in reports for i in r.impulses if i.normal_impulse > 1e-10]
    worst = max(enumerate(reports), key=lambda x: x[1].penetration_after, default=None)
    return dict(body_counts=dict(Counter(type(b.shape).__name__ for b in dynamic)),
                finite_mass_bodies=len(dynamic), static_colliders=sum(b.static for b in bodies),
                steps=result.world.step_count, simulated_seconds=result.world.time,
                finite_states=all(math.isfinite(x) for b in bodies for x in
                                  (*b.state.position, *b.state.velocity, *b.state.orientation, *b.state.omega)),
                max_quaternion_norm_error=max((abs(sum(x*x for x in b.state.orientation)-1) for b in dynamic), default=0.),
                max_penetration_before_m=max((r.penetration_before for r in reports), default=0.),
                max_penetration_after_m=max(depths, default=0.),
                worst_penetration_step=worst[0]+1 if worst else None,
                worst_penetration_pair=worst[1].deepest_pair_after if worst else None,
                final_two_seconds_max_penetration_m=max((r.penetration_after for r in reports[-max(1, round(2/result.dt)):]), default=0.),
                p95_step_max_penetration_m=depths[min(len(depths)-1, int(.95*len(depths)))] if depths else 0.,
                final_penetration_m=reports[-1].penetration_after if reports else 0.,
                body_body_impulse_rows=sum(i.b < 30 for i in impacts),
                body_bin_impulse_rows=sum(i.b >= 30 for i in impacts),
                correction_cap_body_steps=sum(r.correction_caps for r in reports),
                kinetic_energy_final_j=kinetic_energy(result.world),
                maximum_final_speed_m_s=max((math.hypot(*b.state.velocity) for b in dynamic), default=0.),
                physics_loop_seconds=result.physics_seconds,
                timing_scope='step_world, contact diagnostics, reports and optional frame sampling; excludes imports, scene setup, rendering and JSON I/O',
                escaped_body_ids=[b.id for b in dynamic if abs(b.state.position[0]) > 2.01 or abs(b.state.position[2]) > 2.01
                                  or b.state.position[1] < -.01])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--headless', action='store_true')
    mode.add_argument('--show', action='store_true')
    parser.add_argument('--snapshot', type=Path)
    parser.add_argument('--json', type=Path, help='summary and realized initial/final states')
    parser.add_argument('--seed', type=int, default=7)
    parser.add_argument('--dt', type=float, default=1/480)
    parser.add_argument('--steps', type=int, default=2880)
    parser.add_argument('--velocity-iterations', type=int, default=120)
    parser.add_argument('--split-iterations', type=int, default=20)
    parser.add_argument('--backend', choices=['serial', 'parallel'], default='serial')
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--batch-size', type=int, default=4)
    parser.add_argument('--serial-threshold', type=int, default=0)
    args = parser.parse_args(argv)
    if args.steps < 0:
        parser.error('--steps must be nonnegative')
    try:
        opts = Options(dt=args.dt, velocity_iterations=args.velocity_iterations, split_iterations=args.split_iterations)
    except ValueError as exc:
        parser.error(str(exc))
    initial = make_scene(args.seed)
    visual = args.show or args.snapshot
    result = simulate(initial, opts, args.steps, backend=args.backend, workers=args.workers,
                      batch_size=args.batch_size, serial_threshold=args.serial_threshold,
                      frame_stride=max(1, round(1/(30*opts.dt))) if visual else None)
    report = summary(result)
    report['backend'] = args.backend
    report['backend_statistics'] = result.backend_statistics
    if visual:
        from .rendering import render
        started = time.perf_counter()
        render(result.frames, snapshot=args.snapshot, show=args.show)
        report['rendering_and_optional_gui_wait_seconds'] = time.perf_counter()-started
    print(json.dumps(report, indent=2, allow_nan=False))
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(dict(summary=report, options=asdict(opts), initial=asdict(initial), final=asdict(result.world)),
                                       indent=2, allow_nan=False), encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
