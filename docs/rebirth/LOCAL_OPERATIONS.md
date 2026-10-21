# Run Rebirth as a local service

Use the detached launcher when you want the game to keep running after the launching terminal closes:

```sh
./scripts/start_rebirth.sh
./scripts/start_rebirth.sh --status
./scripts/start_rebirth.sh --stop
```

The game listens only at `http://127.0.0.1:8782/`. The default save is this checkout's `.kalends/rebirth_session.json`. Logs and a process record are in `.kalends/rebirth_server_8782.log` and `.kalends/rebirth_server_8782.json`. Stopping the service preserves the save. Restarting loads and verifies its accepted command journal. The launcher uses the same Python3.10+ selection as the foreground runner.

A separate QA life needs both a different port and a different journal:

```sh
./scripts/start_rebirth.sh --port 8786 --journal /tmp/kalends-my-qa-life.json
./scripts/start_rebirth.sh --port 8786 --status
./scripts/start_rebirth.sh --port 8786 --stop
```

A checkout-wide lock serializes launcher operations. An existing Rebirth service is recognized by its local `/api/state` version4 response and reused; an unrelated occupied port is left alone. Two managed servers cannot write the same journal concurrently. An unmanaged existing service can be reused, but the launcher does not adopt its PID and will not stop it. Use that service's original terminal to stop it. If a managed port already has a different journal, choose another port or explicitly stop the managed life first.

Before sending SIGTERM, `--stop` checks the recorded checkout and current process command against the Python executable, Rebirth module, port and absolute journal. A stale or unrelated PID is not signalled. It does not escalate to SIGKILL. The launcher does not register an OS login agent: a reboot or a host process manager can still end the service. After a reboot, run the same start command again. The service remains local; this is not public hosting.

The foreground path remains available:

```sh
./scripts/run_rebirth.sh
./scripts/run_rebirth.sh --temporary --port 8784
```

The background launcher deliberately omits migration and unsaved-life switches. For legacy continuation, use the existing foreground runner with `--migrate-from OLD --journal DIFFERENT_NEW`, verify the new life, stop it, then start the managed service with that new journal. Old journals are never intentionally overwritten or removed by these launchers.

## Verified lifecycle

On 21 October 2026, an isolated 8786 QA service survived its launching command; a repeated start reused its PID; status succeeded; a second port using the same save was refused. A real three-minute advance persisted, stopping preserved the exact journal bytes, and restarting recovered its minute and ledger hash. A separate unrelated HTTP service was left running, and a deliberately mismatched process record did not cause its live sleep process to be signalled. The QA game and auxiliary test processes were then stopped. These are local process/save checks, not a guarantee of uptime or a replacement for storage capacity.
