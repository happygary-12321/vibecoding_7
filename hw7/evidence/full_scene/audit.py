"""Saved-state acceptance using the original Part 2 analytic limits."""
import math
from hw7.evidence.audit_default import extent


def accept(data):
    summary, initial, final = data['summary'], data['initial'], data['final']
    assert len(initial['bodies']) == len(final['bodies']) == 35
    assert [b['id'] for b in initial['bodies']] == [b['id'] for b in final['bodies']] == list(range(35))
    assert sum(not b['static'] for b in final['bodies']) == 30
    assert sum(b['static'] for b in final['bodies']) == 5
    assert initial['step_count'] == 0 and initial['time'] == 0 and not initial['cache']
    assert summary['finite_mass_bodies'] == 30 and summary['static_colliders'] == 5
    assert summary['body_counts'] == {'Prism': 10, 'Sphere': 10, 'Cylinder': 10}
    assert summary['steps'] == final['step_count'] == 2880
    assert abs(summary['simulated_seconds']-6) < 1e-10 and abs(final['time']-6) < 1e-10
    assert summary['finite_states'] and summary['max_quaternion_norm_error'] <= 1e-12
    assert summary['max_penetration_after_m'] <= .03
    assert summary['final_two_seconds_max_penetration_m'] <= .01
    assert summary['final_penetration_m'] <= .01
    assert summary['body_body_impulse_rows'] > 0 and summary['body_bin_impulse_rows'] > 0
    outside, bounds = [], []
    quaternion_error = 0.
    for old, body in zip(initial['bodies'], final['bodies']):
        s = body['state']
        assert all(math.isfinite(x) for key in ('position', 'velocity', 'orientation', 'omega') for x in s[key])
        quaternion_error = max(quaternion_error, abs(sum(x*x for x in s['orientation'])-1))
        if body['static']:
            assert body == old
            continue
        assert s['step_count'] == 2880 and abs(s['time']-6) < 1e-10
        half = [extent(body, j) for j in range(3)]
        lo = [x-r for x, r in zip(s['position'], half)]
        hi = [x+r for x, r in zip(s['position'], half)]
        bounds.append(dict(id=body['id'], minimum=lo, maximum=hi))
        if any(lo[j] < -2.01 or hi[j] > 2.01 for j in (0, 2)) or lo[1] < -.01 or hi[1] > 2.41:
            outside.append(body['id'])
    assert quaternion_error <= 1e-12
    assert not outside, f'full analytic geometry outside tolerance: {outside}'
    return dict(accepted=True, full_geometry_outside_ids=outside, analytic_final_bounds=bounds,
                unchanged_static_bodies=5, dynamic_bodies=30, completed_steps=2880,
                quaternion_norm_error=quaternion_error, limits=dict(transient_m=.03, final_window_m=.01,
                    xz_abs_m=2.01, bottom_m=-.01, top_m=2.41), summary=summary)
