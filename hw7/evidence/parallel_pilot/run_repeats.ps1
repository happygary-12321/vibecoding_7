$ErrorActionPreference = 'Stop'
# Sequential, alternating configuration order; no competing benchmarks.
# Run from repository root. Each label refuses overwrite.
$pilotPython = 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe'
foreach ($scene in @('peak', 'impacts', 'pile')) {
    foreach ($repeat in 0..2) {
        $order = if ($repeat -eq 1) { @(8, 4, 0) } else { @(0, 4, 8) }
        foreach ($workers in $order) {
            $backend = if ($workers -eq 0) { 'serial' } else { 'parallel' }
            $label = 'repeat_{0}_w{1}_r{2}' -f $scene,$workers,$repeat
            $pilotWatch = [Diagnostics.Stopwatch]::StartNew()
            & $pilotPython -B -m hw7.parallel_pilot measure --label $label --scenes $scene --backend $backend --workers ([Math]::Max(1,$workers)) --batch-size 4 --repeats 1 --reference-label validation_v3
            $pilotExit = $LASTEXITCODE
            $pilotWatch.Stop()
            @{exit_code=$pilotExit; cold_invocation_seconds=$pilotWatch.Elapsed.TotalSeconds; sequence_repeat=$repeat; sequence_workers=$workers} |
                ConvertTo-Json | Set-Content -Encoding UTF8 ('hw7/evidence/parallel_pilot/{0}/cold_invocation.json' -f $label)
            if ($pilotExit -ne 0) { throw "Trial $label failed: $pilotExit" }
        }
    }
}
