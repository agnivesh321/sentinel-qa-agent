# Sentinel Release Guard

AlgoFest Hackathon 2026 submission for the **AI/ML** and **Open Innovation** tracks.

The full project package is here:

```text
algofest_sentinel_release_guard/
```

## Elevator Pitch

Sentinel Release Guard is an AI release-risk agent that reads risky software changes, generates security regression gates, simulates CI evidence, and blocks unsafe releases before production.

## Run The Demo

```powershell
python algofest_sentinel_release_guard\sentinel_release_guard.py demo
python -m unittest discover -s algofest_sentinel_release_guard\tests
```

Open:

```text
algofest_sentinel_release_guard\demo_output\dashboard.html
```

## What Judges Should Review

- `algofest_sentinel_release_guard/README.md`
- `algofest_sentinel_release_guard/demo_output/dashboard.html`
- `algofest_sentinel_release_guard/demo_output/sentinel_report.md`
- `algofest_sentinel_release_guard/demo_output/benchmark_summary.md`
- `algofest_sentinel_release_guard/sentinel_release_guard.py`

This branch is dedicated to the AlgoFest submission. The repository's `main` branch remains available for the earlier Sentinel QA Agent package.
