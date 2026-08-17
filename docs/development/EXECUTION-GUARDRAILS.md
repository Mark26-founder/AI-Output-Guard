# EXECUTION-GUARDRAILS.md

## Purpose

This file defines execution behaviour for the AI Output Guard coding agent.

The existing project files define the product, requirements, architecture, implementation sequence, and current state.

This file defines how the agent must behave while executing those instructions.

Do not duplicate or replace information from:
- AI-CONSTITUTION.md
- PROJECT.md
- REQUIREMENTS.md
- ARCHITECTURE.md
- IMPLEMENTATION_PLAN.md
- PROGRESS.json

Those files remain authoritative for their respective purposes.

---

## 1. Scope Control

Work only on the explicitly assigned current task.

Before changing anything:

1. Read `PROGRESS.json`.
2. Identify the current phase and task.
3. Read only the project documents necessary to execute that task.
4. Inspect only relevant source, test, and configuration files.

Do not implement future phases.

Do not add features because they might be useful later.

Do not redesign the architecture unless the current task explicitly requires it or an existing design is proven to be invalid.

If the task is already complete, verify it instead of rebuilding it.

---

## 2. Token Efficiency

Minimize unnecessary context, analysis, tool calls, and output.

Rules:

- Do not scan the entire repository unless the task genuinely requires it.
- Do not repeatedly read files that have already been inspected and understood.
- Do not reread the entire project plan for every task.
- Use targeted file searches instead of broad searches.
- Open only relevant sections of files when possible.
- Prefer one precise command over several exploratory commands.
- Do not generate unnecessary documentation, comments, abstractions, or examples.
- Do not explain implementation details before implementation unless clarification is necessary.
- Do not repeat information already contained in project files.
- Do not investigate unrelated warnings or files.
- Do not use tools that provide no direct value to the current task.
- After successful verification, stop.

Optimize for:

`minimum necessary work → verified result → stop`

Do not sacrifice correctness merely to save tokens.

---

## 3. Source-of-Truth Discipline

Follow the project's existing authority hierarchy.

Do not invent requirements when the project documentation already defines them.

If two project documents appear to conflict:

1. Follow the established authority hierarchy.
2. Do not silently choose a convenient interpretation.
3. Stop and report the conflict if it materially affects implementation.

Do not replace an unresolved architectural decision with an arbitrary implementation choice merely to keep moving.

---

## 4. Implementation Discipline

Implement the smallest correct solution that satisfies the current task.

Prefer:

- existing project patterns
- standard Python mechanisms
- already-approved dependencies
- simple, explicit code
- narrowly scoped changes

Avoid:

- speculative abstractions
- premature generalisation
- unnecessary dependencies
- custom frameworks
- duplicate infrastructure
- unrelated refactoring
- broad cleanup
- changing public APIs without requirement

Every changed file must have a direct reason related to the current task.

---

## 5. Dependency Discipline

Do not add a dependency merely because it makes implementation slightly easier.

Before adding a dependency, establish that:

- the current task genuinely requires it;
- an existing dependency or standard-library solution is insufficient;
- it is compatible with the project's requirements;
- its addition does not create unnecessary architectural complexity.

If dependency selection is an unresolved project decision, do not guess. Stop and report it.

---

## 6. Debugging Protocol

When something fails:

1. Read the actual error.
2. Identify the likely root cause.
3. Inspect only the files/configuration relevant to that cause.
4. Make one concrete fix.
5. Verify the fix.

Do not make random changes.

Do not repeatedly rerun the same failing command without changing the relevant cause.

Do not speculate through multiple unrelated fixes.

---

## 7. Three-Attempt Limit

For each distinct issue, maximum three genuine fix attempts are allowed.

An attempt counts only when it includes a meaningful change based on the observed failure.

After three unsuccessful genuine attempts:

STOP.

Do not continue experimenting merely to consume more tokens.

Report:

- exact error;
- suspected root cause;
- attempts made;
- files changed;
- verification results;
- whether the blocker is code, configuration, dependency, environment, specification, or architecture;
- what intervention or decision is required;
- exact stopping point.

A new root cause discovered later may be treated as a distinct issue, but do not artificially split one problem into multiple attempts to bypass this rule.

---

## 8. Hard Stop Conditions

Stop instead of continuing when:

- the task requires an unresolved architectural decision;
- project requirements conflict materially;
- a required dependency cannot be resolved;
- the environment prevents reliable verification;
- the same issue remains unresolved after three genuine attempts;
- continuing would require weakening requirements;
- continuing would require disabling tests or quality checks;
- the only apparent solution is speculative or unrelated to the task;
- the requested change would violate the project's authority hierarchy.

Never hide a blocker.

Never claim completion when verification has not established completion.

---

## 9. No Verification Bypass

Never:

- disable tests to make them pass;
- weaken assertions merely to obtain green tests;
- suppress meaningful errors;
- bypass type checking without justification;
- bypass linting without justification;
- remove requirements because implementation is difficult;
- modify verification commands merely to avoid failures;
- mark incomplete work as complete.

Fix the underlying problem or stop.

---

## 10. Verification Discipline

A task is complete only when its required acceptance criteria are satisfied.

Use the smallest verification set that proves the task.

For project phases, follow the verification gates defined in `IMPLEMENTATION_PLAN.md`.

Do not run expensive or unrelated verification merely for appearance.

Do not skip required verification.

After verification succeeds:

1. update the appropriate progress state;
2. record the actual completed work;
3. record any remaining work;
4. stop.

---

## 11. Session Discipline

Each session should have one primary objective: complete the currently assigned task.

Do not continue into the next phase simply because the current phase finished early.

When the current task is complete:

`verify → update progress → stop`

The next phase should begin only through a new explicit task/instruction.

---

## 12. File Modification Discipline

Before editing a file, understand why it needs to change.

Do not modify:

- unrelated source files;
- unrelated tests;
- documentation unrelated to the task;
- configuration unrelated to the task;
- generated files unless required.

Keep changes local and reviewable.

Do not perform broad formatting or refactoring across the repository unless explicitly required.

---

## 13. Communication Discipline

Keep progress reports concise and factual.

When successful, report:

- what was completed;
- files changed;
- verification performed;
- current progress state;
- next required task.

Do not provide lengthy explanations of routine implementation work.

When blocked, provide the complete blocker report defined in Section 7.

Do not claim certainty when the evidence does not support it.

---

## 14. Project-Specific Phase Discipline

AI Output Guard is intentionally developed sequentially.

Follow:

`P0 → verification → P1 → verification → P2 → ... → P10`

Do not implement later-phase functionality during an earlier phase.

If a later-phase question becomes relevant, record it as an unresolved decision and continue only if the current task can proceed without resolving it.

If it cannot proceed, stop and report the decision required.

---

## 15. Default Execution Loop

For every task:

1. Read `PROGRESS.json`.
2. Identify the exact current task.
3. Read the minimum relevant project documentation.
4. Inspect only relevant files.
5. Implement the smallest correct change.
6. Run targeted verification.
7. Diagnose failures from actual evidence.
8. Apply the three-attempt limit.
9. Run the required phase verification gate.
10. Update `PROGRESS.json`.
11. Report concise status.
12. Stop.

---

## 16. Core Principle

The agent is not rewarded for doing more work.

It is rewarded for producing the correct result with the minimum necessary work.

Therefore:

`Do not explore when you can inspect.`

`Do not inspect when you already know.`

`Do not change when nothing requires changing.`

`Do not retry without a new diagnosis.`

`Do not continue after a hard stop.`

`Do not implement tomorrow's work today.`

`Verify, checkpoint, and stop.`
