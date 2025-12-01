# Testing Improvements TODOs

- [ ] Run identical cases across a model matrix (mini, standard, etc.) and diff summaries/metrics.
- [ ] Emit red/green visual artifacts per case with expectation checklist and timeline highlights.
- [ ] Keep lightweight success reports for quick confirmation when everything passes.
- [ ] Add response time and tool-usage assertions directly to each test case.
- [ ] Record cost/latency metrics for regression tracking.
- [ ] Validate structured response formats (JSON, tables, lists) before marking passes.
- [ ] Enforce consistent response styles ready for downstream parsing.
- [ ] Introduce declarative tool-call pattern operators (star, plus, optional, exact, range).
- [ ] Support pattern lists like `[search_products, ToolCallStar, ToolCallPlus(get_sales_data)]` in specs.
- [ ] Build enhanced error reporting with clearer diffs and debugging context.
- [ ] Add data state assertions decoupled from case definitions.
- [ ] Integrate external systems or fixtures to drive richer scenarios.
- [ ] Benchmark performance across runs and fail on regressions.
- [ ] Create visual dashboards summarizing run health.

- [ ] Run the full suite multiple times to surface flaky behavior.
- [ ] Support expected tool-call operators for `in`, `set`, `list`, etc.
- [ ] Let testing agents call helper agents/tools for due diligence.
- [ ] Evaluate Goose core once per session, not after every test.
- [ ] Detect whether failures stem from tool errors or agent reasoning mistakes.
