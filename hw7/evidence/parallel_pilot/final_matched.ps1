param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
# PLANNED FINAL WORK ONLY. Not invoked by Part 4.
# Three full runs/backend, sequential, alternating order; new labels required.
foreach ($repeat in 0..2) {
    $order = if ($repeat -eq 1) { @('parallel', 'serial') } else { @('serial', 'parallel') }
    foreach ($backend in $order) {
        $label = 'final_{0}_r{1}' -f $backend,$repeat
        $arguments = @('-B', '-m', 'hw7.parallel_pilot', 'measure', '--label', $label,
            '--scenes', 'full', '--backend', $backend, '--workers', '8', '--batch-size', '4',
            '--serial-threshold', '0', '--steps', '2880', '--warmup-steps', '30', '--repeats', '1')
        if ($backend -eq 'parallel' -or $repeat -gt 0) { $arguments += @('--reference-label', 'final_serial_r0') }
        $pilotWatch = [Diagnostics.Stopwatch]::StartNew()
        & $Python @arguments
        $pilotExit = $LASTEXITCODE
        $pilotWatch.Stop()
        @{exit_code=$pilotExit; cold_invocation_seconds=$pilotWatch.Elapsed.TotalSeconds; sequence_repeat=$repeat; sequence_backend=$backend} |
            ConvertTo-Json | Set-Content -Encoding UTF8 ('hw7/evidence/parallel_pilot/{0}/cold_invocation.json' -f $label)
        if ($pilotExit -ne 0) { throw "Full trial $label failed: $pilotExit" }
    }
}
