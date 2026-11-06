# Part 5 complete-scene comparison

| Trial | Backend | Stepping seconds | Cold seconds |
| --- | --- | --- | --- |
| full_serial_r0 | serial | 1047.9100364 | 1056.8112320 |
| full_parallel_r0 | parallel | 381.9162382 | 388.4043114 |
| full_parallel_r1 | parallel | 376.7153257 | 383.2620153 |
| full_serial_r1 | serial | 1066.6222320 | 1075.2671255 |
| full_serial_r2 | serial | 1066.8177625 | 1075.8132584 |
| full_parallel_r2 | parallel | 377.2070056 | 383.9497146 |

Median stepping speedup: 2.827684x; cold invocation speedup: 2.800542x.

All six complete World/cache/report canonical digests match exactly; all saved-state acceptance audits pass.

See comparison.json for sample SD/range, raw overhead, dispatch/PID work, scope and limitations.
