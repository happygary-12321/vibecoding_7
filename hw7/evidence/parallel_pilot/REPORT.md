# Part 4 interval comparison

Three 30-step (.0625 simulated second) cached intervals, not the complete 2880-step scene.

| Interval | Workers/batch | Raw stepping seconds | Median ± sample SD | Speedup |
| --- | --- | --- | --- | --- |
| peak | 0/4 | 12.6433017, 12.5864567, 13.1268164 | 12.6433017 ± 0.2969305 | 1.000x |
| peak | 4/4 | 4.5984833, 4.6139579, 4.5568106 | 4.5984833 ± 0.0295575 | 2.749x |
| peak | 8/4 | 3.7392719, 3.6147029, 3.6541155 | 3.6541155 ± 0.0636689 | 3.460x |
| impacts | 0/4 | 5.7040663, 5.7273241, 5.6695913 | 5.7040663 ± 0.0290475 | 1.000x |
| impacts | 4/4 | 2.7347167, 2.6927825, 2.7306732 | 2.7306732 ± 0.0231320 | 2.089x |
| impacts | 8/4 | 2.6700993, 2.6722559, 2.6576842 | 2.6700993 ± 0.0078647 | 2.136x |
| pile | 0/4 | 14.9351282, 14.8250897, 14.3579822 | 14.8250897 ± 0.3064298 | 1.000x |
| pile | 4/4 | 5.0691963, 5.1243991, 4.8760941 | 5.0691963 ± 0.1303784 | 2.925x |
| pile | 8/4 | 4.2089745, 4.1804853, 4.1894319 | 4.1894319 ± 0.0145693 | 3.539x |

Recommended preliminary setting: 8 workers, batch 4, threshold 0.

Historical serial pickle digests reproduced; direct Python serial/parallel equality passed in validation_v3. Every screen/repeat canonical value digest exactly equals that reference.

Unprofiled entire stepping/report loop, both detection barriers, all IPC/gather/synchronization and unchanged serial solver; excludes load/setup/warmup/output/rendering, no frame sampling.

4 discarded steps from same genuine starting world, reset physical/cache state before timing; pool reused across warmup and measured steps; fresh pool per trial.

Caller cold_invocation includes Python process/imports, checkpoint validation/loading, readiness, warmup, stepping, digest construction, shutdown, output. It excludes the wrapper JSON write.

All unsuccessful batch-size/configuration results remain in screen_v1/.

No complete 2880-step comparison was run.
