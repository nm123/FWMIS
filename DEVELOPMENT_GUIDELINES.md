# FWMIS Development Guidelines

## Cost Optimization Rules

### Model Selection Priority
- **Primary**: deepseek-r1-0528 (excellent for Python, 92%+ HumanEval)
- **Secondary**: grok-code-fast-1 (fast debugging and testing)
- **Tertiary**: Other free-tier models (deepseek-v3.1, gemini-2.5-pro, gpt-5-high)
- **Paid**: Only when free models fail to deliver robust fixes

### Request Patterns
- Always start with: "Use deepseek-r1-0528 for this task"
- Be specific about scope and requirements
- Break complex tasks into smaller, manageable pieces
- Focus on incremental improvements

### Budget Management
- Monitor Cursor usage dashboard regularly
- Set usage alerts if available
- Track quota consumption patterns
- Aim for 90%+ free model usage

## Project Context
- **Application**: FWMIS (Fruitless and Wasteful Expenditure Management Information System)
- **Tech Stack**: Python, PyQt5, SQLite
- **Status**: Performance optimizations implemented and working
- **Focus**: Incremental improvements, new features, maintenance

## Development Workflow
1. **Start Simple**: Use free models for initial implementation
2. **Iterate**: Refine with free models
3. **Test**: Validate with free models
4. **Escalate**: Only if free models hit limitations
5. **Document**: Update guidelines based on learnings

## Quality Tooling
- **Linting**: `ruff check scripts tests` (formatting fixes with `ruff check --select I --fix scripts tests` to autofix imports).
- **Type Checking**: `mypy scripts` using the repo configuration.
- **Test Suite**: `pytest` for unit/performance smoke tests.
- **Environment**: Install dev extras with `uv pip install .[dev]` (or `pip install .[dev]`).

## Emergency Escalation Criteria
- Free models consistently fail to solve the problem
- Complex architectural decisions required
- Critical production issues need immediate resolution
- User explicitly requests paid model for specific reason
