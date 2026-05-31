# Judge Checklist

## What To Open First

1. `README.md`
2. `demo_output/dashboard.html`
3. `demo_output/sentinel_report.md`
4. `demo_output/benchmark_summary.md`
5. `sentinel_release_guard.py`

## What To Run

```powershell
python algofest_sentinel_release_guard\sentinel_release_guard.py demo
python -m unittest discover -s algofest_sentinel_release_guard\tests
```

## What To Notice

- The project is runnable without paid APIs.
- The agent makes an explicit release decision.
- The decision is supported by risk signals and generated tests.
- High-risk failures create a human review queue.
- Benchmark cases show high, medium, and low-risk behavior.
- The project can become a real CI/CD product.
