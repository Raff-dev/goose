# Future Testing Framework Improvements

## 🎯 **Proposed Enhancements for Agent Behavior Testing**

### **0. Model Matrix + Visual Reports (High-Value Additions)**

#### Model Matrix (multi-model runs)
- Run the same case across a small matrix of models (e.g., gpt-4o-mini, gpt-4o) and compare behavior.
- Output: per-model summary (pass/fail, tokens, latency, tool counts) and a compact diff of tool-call sequences and response format compliance.

#### Visualisation on failure/success (red/green checks)
- Generate an artifact per case with red/green checkmarks for each expectation, tool-call timeline with mismatches highlighted, and key metrics.
- On success, optionally emit a lightweight "green" report.

#### Why it matters
- Immediate triage: see exactly which expectation failed and how tool usage diverged.
- Encourages adding expectations because feedback becomes fast and visual.

### **1. Time Constraints & Performance Validation**

Add performance assertions to test cases to ensure agent responses are timely and efficient.

#### **Benefits:**
- **Performance Testing**: Ensure agents respond within acceptable time limits
- **Efficiency Validation**: Prevent excessive tool usage
- **Resource Monitoring**: Track computational costs
- **Regression Prevention**: Catch performance degradation

### **2. Response Format Validation**

Validate that agent responses conform to expected output formats (JSON, tables, lists, etc.).

#### **Benefits:**
- **Structured Output**: Ensure agents produce expected formats
- **Parseability**: Guarantee outputs can be processed by other systems
- **Consistency**: Maintain uniform response styles
- **Integration Ready**: Outputs ready for downstream processing

### **Tool call pattern types (details to implement later)**
Add explicit pattern classes to make tool-call assertions expressive and composable.

- `ToolCallStar` — wildcard that matches any single tool call or sequence placeholder.
- `ToolCallPlus(tool)` — requires that `tool` is called at least once.
- `ToolCallOptional(tool)` — the named tool may or may not appear.
- `ToolCallExact(tool, count=n)` — the named `tool` must be called exactly `n` times.
- `ToolCallRange(tool, min=m, max=n)` — the named `tool` must be called between `m` and `n` times.

Example use in test spec: sequence patterns like `[search_products, ToolCallStar, ToolCallPlus(get_sales_data)]`

---

## **📋 Implementation Priority**

### **Phase 1: Core Features**
1. ✅ Basic case validation with expectations
2. ✅ Tool call pattern matching (`ToolCallStar`, `ToolCallPlus`)
3. ✅ Data setup/cleanup (`Product.create()`)

### **Phase 2: Performance & Quality**
1. **Time Constraints** - Performance validation
2. **Response Format Validation** - Output structure validation
3. Model Matrix + Visual Failure/Success Reports (red/green checks)
4. Enhanced error reporting and debugging

### **Phase 3: Advanced Features**
1. Data state assertions (separate from case definition)
2. Integration with external systems
3. Performance benchmarking and regression detection
4. Visual test result dashboards

---

## **🔧 Technical Considerations**

### **Determinism & Drift (Seeding Notes)**
- OpenAI models offer a `seed` parameter in newer APIs for reduced variance within short windows.
- Seeding does NOT guarantee perfect reproducibility across time due to backend changes.
- Practical approach: normalize outputs, compare tool-call sequences and response format compliance rather than full-text equality, track model versions in artifacts.


# multiple steps


# test whether error was a result of the tool or the agent messed up

# run multiple times

# test agents with other agents - we could add additional tools so the testing agent could do its own due dilligence

# move error up top
# for each expected tool show ticks too
# divide test cards by file
# when run all, on test card error_type is not visible untill all runs finish, the same for test detail
# test name too long in the card
# expected tool call operators in, set, list, etc.
# evaluate goose only once, not after every test
