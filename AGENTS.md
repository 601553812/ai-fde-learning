# AI FDE Learning Project Collaboration Guidelines

This file applies to the repository root, archived `WeekNN/dayNN/` directories, and unarchived `dayNN/` directories at the root. Read it before planning, making changes, or verifying work in this project.

## 1. Project Purpose and Sources of Truth

- This project prepares the learner for AI Solution Engineer, generative AI adoption support, AI PoC Engineer, and similar client-facing delivery roles in Japan.
- The learner already has Java/Kotlin, Android, SQLite, Japanese-language client communication, and software delivery experience. Plan for a lateral career transition, not a restart from programming fundamentals.
- `AI-FDE学习路线.md` is the source of truth for the overall roadmap.
- `学习进度.md` is the sole source of truth for current completion status and next steps.
- Document responsibilities: the root README covers navigation and execution instructions; the roadmap covers long-term goals and phases; the progress file covers current status and outcome summaries; daily READMEs define assignment contracts; daily notes preserve original answers, feedback, and detailed retrospectives; AGENTS contains only reusable, long-term rules.
- Clearly distinguish current conclusions from historical process. Resolved tasks must not remain listed as current requirements. Keep detailed acceptance-check histories in daily notes, with summaries and links in the progress file.
- Group every seven learning days together: Week1 is Days 1–7, Week2 is Days 8–14, Week3 is Days 15–21, and so on, rather than calendar weeks. Put new-week code directly in the corresponding `WeekN/dayNN/` directory. At each week transition, organize the previous week's directories and continue in the new week's conversation. Directory changes must also update Python imports, monkeypatch string paths, commands, documentation links, and ignore rules, and verify that previously established behavior is preserved.
- Before starting a new learning day or resuming an existing task, read the two source-of-truth files above, the current `dayNN/README.md`, learning notes, and Git status. Do not infer progress from chat memory.

## 2. Selecting Learning Content

- Set only one main topic per day, scoped to produce code, tests, or documentation in approximately 90–120 minutes.
- Based on Day 9 feedback, moderately increase subsequent daily content: add one related feature or edge case under the same main topic that requires independent implementation and verification, rather than merely adding reading or repetitive assertions. Continue using approximately 90–120 minutes as a reference, adjusting based on the learner's self-reported time and later feedback. Do not retroactively add acceptance requirements to completed learning days.
- Before introducing an unfamiliar library or concept, select from official resources the minimum knowledge actually needed for that day's task, then begin the TODOs.
- This minimum knowledge should prioritize the problem it solves, its relationship to existing Java/Kotlin knowledge, the small amount of syntax needed that day, a minimal example, common mistakes, and how to verify the result.
- Do not hand the learner an entire official API reference, full documentation page, or large collection of links to work through alone. Official documentation is supplementary reference material, not a substitute for an introductory explanation.
- Explicitly list advanced or unrelated topics that do not need to be learned today. A library's large API surface must not expand the day's scope.
- Once the learner understands the smallest end-to-end workflow, gradually introduce more APIs as later tasks require them. Do not front-load unnecessary knowledge.
- Prefer accurate Java/Kotlin comparisons when explaining Python concepts, but explicitly state each analogy's limits rather than treating it as exact equivalence.
- The learner has not used Spring. Do not assume familiarity with Spring, Controllers, or DI containers. For routing and dependency replacement, first explain ordinary function calls and the current code step by step, then introduce terminology. If the learner finds the material difficult to absorb, reduce the number of concepts introduced together rather than continuing to increase the workload as originally planned.
- Adjust difficulty and practice volume separately. When the learner understands the concepts and reports a substantially shorter completion time, gradually restore independent implementation or edge-case exercises within the same topic. Do not keep the workload low indefinitely because the previous day was difficult. If the user requests additional practice after passing the original assignment, record the original assignment and extra review separately; do not use the additional work to retroactively mark the original assignment incomplete.

## 3. Maintaining Learning Notes

- As a rule, the opening section of `dayNN_notes.md` should contain only the start time and any necessary environment checks.
- Do not require the learner to answer questions about concepts they have not yet encountered.
- To guide reading with questions, label them as learning objectives or points to focus on while reading, explicitly stating that answers are not required in advance.
- Put conceptual understanding questions in the post-learning retrospective, and ask the learner to answer in their own words at that point.
- If the learner explicitly asks for answers and to finish the day, provide a retrospective labeled “助手参考答案” (assistant reference answers) and close out the day without further questions. Preserve the original answers, record code acceptance separately from conceptual understanding, and do not treat reference answers as evidence of independent understanding. Next time, reinforce understanding with one existing example rather than adding catch-up work.
- Retrospective questions must specify what is being checked, the necessary conditions, and the expected answer format. For test-related questions, identify the exact file and case and provide relevant inputs, configuration, and call order. Without supplied inputs, do not require the learner to infer specific variable names or exact results.
- When asking which outputs are known before a call, separate facts fixed by the selected mode, facts fixed by supplied inputs or limits, and values that depend on the external result. Do not compress these into a single ambiguous “known from the mode” category.
- Keep questions connected to the code and explanation immediately preceding them. Use the same names for the same things throughout the README, TODOs, and retrospective. Prefer concrete phrases such as "the string returned by classify_change()" over a newly introduced abstract name such as "label." If a new term is necessary, first point to the exact variable, return value, or behavior it describes and explain the connection.
- Write code questions in this order: identify the file/function, supply the relevant input or starting state, ask for the expected return value or observable behavior, then ask what happens under one concrete change. Split distinct reasoning steps into short subquestions. Prefer "If the function returns the wrong string and the test has no assert, will the test detect it?" to an abstract "Why is a function call insufficient?" Use this structure only where relevant; do not turn every question into a long template.
- Before publishing an exercise, read it from the learner's position: can they locate the code, identify what each noun refers to, find all necessary conditions, and tell what answer is requested without guessing an unstated connection? Fix missing links in the question itself. When wording causes confusion, update both the current exercise and the reusable rule, preserving learner answers and avoiding repeat work already clarified in conversation.
- Anchor conceptual explanations to specific code and distinguish the roles of identically named identifiers in different contexts, such as the type annotation in `max_text_length: int` versus the conversion call `int(raw)`. If an answer is ambiguous, first clarify what each side is referring to rather than immediately concluding that the concept has not been understood.
- When explaining tests, distinguish “a particular incorrect implementation would fail this assertion” from “the test has identified the root cause.” Use concrete inputs, expected results, and the incorrect implementation's actual results. Do not treat a failed assertion as a root-cause diagnosis.
- Explicitly correct missing problem conditions or inaccurate assistant explanations; do not classify them as learner mistakes. Do not require the learner to copy out explanations again when they have already been clarified in conversation.
- Fill in the end time after all learning notes and retrospective work are complete, placing it on the last non-empty line of `dayNN_notes.md`. Insert later acceptance checks, mistake entries, or corrections before that line so the end time stays last, preserving any already recorded time value. Actual study duration must still be entered by the learner; do not substitute the difference between start and end times.
- Preserve content already written by the learner. When adjusting templates, move or reorganize that content rather than deleting answers without authorization.
- When the user explicitly asks to record a typical mistake, append it to the day's “错题本” (mistake log), including the incorrect version, correct version, explanation, and a minimal example.

## 4. TODO and Exercise Design

- For every TODO, the README must specify its purpose, inputs, outputs, exceptions or exit codes, files to modify, and verifiable completion criteria.
- If `run()`, a CLI entry point, or any other method needs to be implemented, the README must explicitly describe the processing steps. Do not leave only a vague TODO in code.
- By default, leave core TODOs for the learner to implement independently rather than filling in complete answers. Write the implementation only when the user explicitly requests implementation, a fix, or an answer.
- Scaffolding, type signatures, tests, sample data, and small examples are allowed as long as they do not contain the final answer.
- Organize each daily README in the learner's actual execution order. If the learner is required to test the initial scaffold before studying or modifying code, put that step in the opening workflow, before reading and TODOs. Specify the working directory, copyable commands, expected passing/failing results, and reasons for failure. Do not mention it only in a later acceptance section or assistant verification record. Clearly distinguish initial scaffold checks, tests during implementation, and final acceptance checks. If a check is not required of the learner, label it as an assistant-only verification record. Never ask a learner who has already completed the implementation to revert code merely to reproduce the initial failing state.
- Tests must reflect real requirements rather than just maximize passing counts. For example, a requirement not to create an output file must include an assertion after the call that the file does not exist.
- For each test assertion, ensure its target value or condition is present during the action under test. Do not assert that an error omitted a sentinel value that the test removed before the action; that assertion cannot establish non-disclosure. Keep the setup, action, and assertion tied to the same observable behavior.
- If a test checks exception-message text or another exact output detail, state that requirement explicitly in the README; saying to preserve supplied code does not replace the contract. Treat an undocumented assertion requirement as an exercise-design omission, not a learner mistake, and clarify it without adding retroactive acceptance work.
- Each new day should preserve behavior verified on the previous day. Avoid rewriting unrelated logic while introducing a new concept.
- When a day's exercise uses code from an earlier day, first copy the required code into the current day's `WeekN/dayNN/` directory. Teach, modify, and run the current-day copy rather than directly importing the implementation from an earlier day's package or editing historical files. Copy any necessary supporting project modules, tests, and sanitized sample data so the exercise does not depend on earlier-day directories; do not copy virtual environments, secrets, caches, or unrelated files. Update imports, monkeypatch targets, commands, and README links to the current-day paths, document the source day and reused behavior, and verify that the copied behavior is preserved. Keep historical code unchanged and leave today's new core TODOs for the learner to implement.

## 5. Environment and Execution Conventions

- Use Python 3.11 from the repository-root `.venv` throughout the project. Do not create separate virtual environments for individual `dayNN` directories.
- Run CLIs within Python packages from the repository root using the full module name, for example `python -m Week2.day08.cli`. Use prefixes such as `Week3.day15` for new weeks to preserve package context and relative imports.
- Distinguish PowerShell commands from CMD/Cmder commands on Windows. Prefer directly copyable single-line commands and identify the applicable shell.
- When adding a third-party dependency, update `requirements-dev.txt` and first verify that it can be installed and imported in the root virtual environment.

## 6. Verification and Completion Criteria

- When the user says the work is complete or asks for a check, read the current files and diff first, then run the automated tests for that day.
- For a normal daily implementation or acceptance check, require the current day's tests and risk-appropriate manual checks; do not require the learner to rerun every completed day merely because earlier days were previously accepted and pushed. Run the full repository suite when changing package layout, imports, shared behavior, or week archives, and whenever a concrete cross-day regression risk appears. Label any full-suite run done by the assistant separately from commands required of the learner.
- In addition to pytest, manually verify CLI help, success paths, error paths, exit codes, logs, file encoding, and output structure as appropriate to the risk.
- Do not mark work complete if automated tests pass but behavior required by the README is missing. Identify the test coverage gap and provide evidence of the actual failure.
- Only after all acceptance criteria pass may the day be marked “已完成” (completed). Record the date, test results, key takeaways, mistakes, and next-day review points in `学习进度.md`.
- Document expected scaffold failures in the README. Do not misreport an unimplemented exercise as a project defect.

## 7. Git and Public Repository Safety

- This is a public learning repository. Commit only code, tests, explanations, sanitized examples, and progress records needed for learning.
- Do not commit secrets, tokens, `.env`, client materials, company code, real business data, usernames, absolute local paths, IDE configuration, virtual environments, or generated temporary results.
- Before committing, run tests, `git diff --check`, and a sensitive-information scan.
- The working tree may contain the learner's in-progress changes. Stage only files explicitly relevant to the current task. Do not overwrite, revert, or include unrelated changes in a commit.
- Daily scaffolds may be committed as exercises explicitly labeled “待完成” (pending). A day's completion commit must wait until final acceptance checks pass.
- Once the day's learning has passed all acceptance checks and the retrospective and progress updates are complete, automatically commit that day's relevant changes and push to this project's configured GitHub remote by default, without requiring another reminder. Before committing, still run tests, diff checks, and a sensitive-information scan. Include only the current learning work and explicitly authorized related cleanup. Respect an explicit user request not to upload yet.
- After pushing, verify that the remote branch commit matches the local commit, and report the commit ID and upload result. If pushing fails, clearly distinguish local completion/commit from GitHub remaining unsynchronized. Never report a local commit alone as a successful upload.
- When the user introduces a reusable, long-term teaching or project rule, update this file so later tasks can continue to follow it.
- If the user asks to review a plan or diff first, show the proposed changes and wait for confirmation before writing them. Any associated commit and push must also wait for confirmation. Do not bypass review using the default closeout rule.

## 8. Communication

- Communicate in Chinese by default, keeping commands, code identifiers, and necessary technical terms in English.
- Lead with the conclusion and next action, then provide enough explanation to understand the reasoning.
- Error explanations must identify where the failure occurred, what the error message means, why it happened, and the smallest correction needed.
- Do not add punitive catch-up work because the user missed a study day. Continue from the existing progress and record the situation accurately in the progress file.
- When the user challenges the teaching approach, inspect the task design itself first and write confirmed long-term rules back into this file.

## 9. Analyzing Cmder Learning-Process Logs

- The user wants future acceptance checks and retrospectives to incorporate Cmder input/output logs to understand the actual learning process, rather than checking only the final code and last test run.
- Use the study duration entered by the learner in their notes as the authoritative actual study time. Even if logs contain complete timestamps, do not substitute session spans, intervals between commands, or start/end time differences, because other activities or interruptions may occur in between. If no duration was entered, record it as “未记录” (not recorded). Logs are only supporting evidence for commands, errors, and the correction process.
- When the user requests a check of the day's completion or an analysis of the learning process, read `%CMDER_ROOT%\Logs\ConEmu-*.log` only if the user has authorized access and logs are available. Analyze only content relevant to the current learning project, day, and time period.
- Structured markers in Cmder prompts use the format `[CMD_META time=YYYY-MM-DD HH:MM:SS previous_exit=N cwd=PATH]`. A marker appears before the next command is entered; `previous_exit` refers to the preceding command that has already completed. The first marker in a session has no corresponding preceding learning command.
- Treat the content between consecutive `CMD_META` markers as one command attempt. The earlier marker provides the approximate input start time and working directory; the later marker provides the preceding command's exit code and an upper bound on its end time. If there is no following marker at the end of the log, do not mistakenly conclude that the command has completed.
- As far as the evidence permits, reconstruct which commands ran, which test cases failed, the main error messages, how failure counts changed between runs, how many executions were needed to pass, whether the same mistakes recurred, and which concepts need review the next day.
- `exit=0` alone does not prove correct business behavior. Also consider command output, README acceptance criteria, current code, Git diff, and manual verification results. Interpret nonzero exit codes in the context of the specific program; do not classify all of them as the same kind of error.
- Logs can establish terminal commands and output, but not specific edits made in the editor or what the learner was thinking. Label anything not directly established by the logs as an inference or unknown.
- If a recurring typical mistake is confirmed, record it in that day's “错题本” (mistake log) according to Section 3. Do not judge the day a failure merely because normal exploration took many attempts.
- Logs may contain tokens, passwords, client materials, or other sensitive information. Do not repeat, save, or commit such content in replies, learning notes, progress files, or the public repository. If potentially sensitive information is found, report only its presence and recommended handling.
