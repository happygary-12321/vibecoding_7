"""Independent acceptance audit of the saved default example, no simulation."""
import json
import math
from pathlib import Path


def extent(body, axis):
    # Test-local quaternion matrix; deliberately no production AABB/support calls.
    w, x, y, z = body['state']['orientation']
    r = ((1-2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y)),
         (2*(x*y+w*z), 1-2*(x*x+z*z), 2*(y*z-w*x)),
         (2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x*x+y*y)))
    shape = body['shape']
    if 'a' in shape:
        return sum(abs(r[axis][j])*shape[key]/2 for j, key in enumerate(('a', 'b', 'c')))
    if 'length' in shape:
        u = r[axis][2]
        return shape['length']/2*abs(u)+shape['radius']*math.sqrt(max(0., 1-u*u))
    return shape['radius']


def main():
    source = Path('hw7/evidence/serial_default.json')
    data = json.loads(source.read_text(encoding='utf-8'))
    summary, final, initial = data['summary'], data['final'], data['initial']
    assert len(initial['bodies']) == len(final['bodies']) == 35
    assert [b['id'] for b in initial['bodies']] == [b['id'] for b in final['bodies']] == list(range(35))
    assert sum(not b['static'] for b in final['bodies']) == 30
    assert summary['finite_mass_bodies'] == 30 and summary['static_colliders'] == 5
    assert summary['body_counts'] == {'Prism': 10, 'Sphere': 10, 'Cylinder': 10}
    assert summary['steps'] == 2880 and abs(summary['simulated_seconds']-6) < 1e-10
    assert summary['finite_states'] and summary['max_quaternion_norm_error'] <= 1e-12
    assert summary['max_penetration_after_m'] <= .03
    assert summary['final_two_seconds_max_penetration_m'] <= .01
    assert summary['body_body_impulse_rows'] > 0 and summary['body_bin_impulse_rows'] > 0
    outside = []
    for old, body in zip(initial['bodies'], final['bodies']):
        if body['static']:
            assert body == old
            continue
        s = body['state']
        assert s['step_count'] == 2880 and abs(s['time']-6) < 1e-10
        assert all(math.isfinite(v) for key in ('position', 'velocity', 'orientation', 'omega') for v in s[key])
        if (any(abs(s['position'][j])+extent(body, j) > 2.01 for j in (0, 2))
                or s['position'][1]-extent(body, 1) < -.01
                or s['position'][1]+extent(body, 1) > 2.41):
            outside.append(body['id'])
    assert not outside, f'full analytic geometry outside bin tolerance: {outside}'
    result = dict(source=str(source), accepted=True, full_geometry_outside_ids=outside,
                  final_max_speed_m_s=summary['maximum_final_speed_m_s'],
                  final_kinetic_j=summary['kinetic_energy_final_j'], summary=summary)
    Path('hw7/evidence/default_audit.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
