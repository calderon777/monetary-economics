# AI-Assisted Tutorials: Independent Subproject Plan

## 1. Purpose

This subproject will help academics convert teacher-authored tutorial questions and indicative answers into structured, AI-assisted formative tutorials.

It will initially live inside the Monetary Economics project, but it must be designed as an independent module that can later be moved into its own repository without breaking either project.

The intended educational model is:

1. A student writes an answer before receiving assistance.
2. AI identifies strengths, omissions, or problems in the reasoning.
3. AI provides a limited hint or diagnostic question rather than a complete answer.
4. The student revises the answer.
5. A human tutor discusses misconceptions and evaluates ambiguous reasoning.
6. An indicative answer is released for reflection and self-checking.

AI is a formative support layer. It is not the academic authority, final marker, or replacement for the human tutor.

## 2. Independence Requirement

The subproject must satisfy the following rule:

> Removing the `ai-assisted-tutorials/` directory must not stop the main Monetary Economics Quarto website from building, except for an optional link or iframe that explicitly points to the subproject.

Similarly, after copying this directory to a new repository:

- the application must run without importing files from the parent project;
- its tests must run without the Monetary Economics course files;
- its documentation and examples must be sufficient for a new academic user;
- no absolute local paths may be used;
- no course-specific API keys, URLs, names, or secrets may be embedded in code;
- deployment must not depend on the parent repository's workflows;
- the parent project must consume the subproject only through a stable public interface.

## 3. Proposed Location and Boundary

Use the following top-level directory:

```text
ai-assisted-tutorials/
```

Everything required by the reusable product should eventually live inside it:

```text
ai-assisted-tutorials/
├── README.md
├── PROJECT_PLAN.md
├── LICENSE
├── pyproject.toml
├── .env.example
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── services/
│   └── ui/
├── tutorials/
│   └── examples/
├── schemas/
│   └── tutorial.schema.json
├── templates/
│   ├── tutorial-questions-template.qmd
│   ├── tutorial-answers-template.qmd
│   └── academic-design-worksheet.md
├── prompts/
│   ├── feedback-system.md
│   └── safety-rules.md
├── scripts/
│   ├── import_qmd.py
│   ├── validate_tutorial.py
│   └── export_tutorial.py
├── tests/
│   ├── fixtures/
│   ├── test_import.py
│   ├── test_schema.py
│   └── test_feedback.py
├── docs/
│   ├── authoring-guide.md
│   ├── deployment-guide.md
│   ├── governance-guide.md
│   └── troubleshooting.md
└── .github/
    └── workflows/
```

The existing `hf-spaces/tutorial-builder/` application can be migrated into this structure in controlled stages. It should not be moved until its current behaviour is covered by tests.

## 4. Relationship with the Main Course Project

The Monetary Economics project should act as a consumer and example implementation, not as a hidden dependency.

The boundary should be:

```text
Monetary Economics course files
          |
          | export/import using a documented schema
          v
Tutorial JSON files
          |
          | stable application interface
          v
AI-Assisted Tutorials application
```

Allowed integration methods:

- a tutorial JSON file conforming to the published schema;
- an iframe pointing to a deployed application URL;
- a URL parameter containing a stable tutorial identifier;
- an optional command-line import of `.qmd` source files;
- a documented HTTP API if one is introduced later.

Disallowed coupling:

- importing Python modules from the parent repository;
- reading `../topicXquestions.qmd` at application runtime;
- relying on the parent `.env`, `requirements.txt`, or GitHub Actions;
- assuming tutorials are called `topic1`, `topic2`, and so on;
- hard-coding Monetary Economics terminology into reusable application logic;
- storing deployment secrets in either repository;
- requiring the parent Quarto site to build the application.

## 5. Canonical Tutorial Data Model

Tutorial JSON must become the canonical interchange format. Quarto files are authoring inputs, not runtime dependencies.

Each tutorial should contain:

```json
{
  "schema_version": "1.0",
  "id": "unique-stable-id",
  "title": "Tutorial title",
  "subject": "Economics",
  "level": "Undergraduate",
  "authors": [],
  "learning_objectives": [],
  "student_instructions": "",
  "ai_policy": {
    "feedback_mode": "diagnostic",
    "reveal_full_answer": false,
    "maximum_feedback_length": 250
  },
  "questions": [],
  "governance": {
    "formative_only": true,
    "ai_disclosure": "",
    "data_collection": "none"
  },
  "metadata": {
    "status": "draft",
    "version": "1.0.0",
    "created_at": "",
    "updated_at": ""
  }
}
```

Each question should have a stable ID and separate fields for:

- question text;
- subquestions;
- relevant context;
- required concepts;
- expected reasoning steps;
- indicative answer;
- acceptable alternative approaches;
- likely misconceptions;
- hint sequence;
- extension questions;
- optional rubric;
- optional reading references.

The schema must be versioned. Schema changes should be backward-compatible where possible and accompanied by a migration script when they are not.

## 6. Academic Authoring Workflow

An academic should be able to create a tutorial without editing application code.

### Step 1: Define the activity

Complete an academic design worksheet covering:

- student level and prior knowledge;
- tutorial purpose;
- learning outcomes;
- evidence expected in a strong answer;
- common misconceptions;
- appropriate AI behaviour;
- prohibited AI behaviour;
- role of the human tutor;
- indicative-answer release policy;
- evaluation method.

### Step 2: Prepare source material

Use paired templates:

- `tutorial-questions-template.qmd`;
- `tutorial-answers-template.qmd`.

Question identifiers must match across the two documents.

### Step 3: Import

Use Teacher mode or a command-line importer to convert the source files into tutorial JSON.

The importer must:

- preview extracted content;
- warn about missing or duplicated question IDs;
- detect unmatched questions and answers;
- preserve Markdown and LaTeX;
- avoid silently discarding unsupported content;
- produce a validation report.

### Step 4: Review

The academic reviews:

- questions;
- indicative answers;
- misconceptions;
- hints;
- AI instructions;
- governance settings.

### Step 5: Test as a student

Test at least:

- a blank answer;
- a superficial answer;
- a confidently incorrect answer;
- a partly correct answer;
- a strong conventional answer;
- a strong alternative answer;
- an attempt to make the AI reveal the complete answer;
- an attempt to override the tutorial instructions.

### Step 6: Approve and publish

Use explicit lifecycle states:

```text
draft -> academically reviewed -> technically tested -> published -> archived
```

The application must not treat an unreviewed draft as published content.

## 7. Feedback Contract

Default AI feedback should:

1. identify what the student has done correctly;
2. diagnose one or two important omissions or errors;
3. explain the type of problem without supplying the complete solution;
4. ask a targeted question or provide a limited hint;
5. invite a revised answer;
6. acknowledge valid alternative approaches;
7. flag uncertainty instead of inventing facts;
8. direct the student to approved materials or a human tutor where necessary.

Default AI feedback should not:

- write a complete answer on the first attempt;
- claim to be the authoritative marker;
- invent references or course rules;
- assign a high-stakes grade;
- expose hidden indicative answers through prompt manipulation;
- treat one wording as the only correct response;
- collect unnecessary personal information.

These defaults should be configurable per tutorial, but weakening core safety and disclosure rules should require an explicit administrator decision.

## 8. Application Architecture

Separate the application into replaceable components:

### Content layer

- tutorial schema;
- JSON loading and validation;
- `.qmd` import and export;
- tutorial versioning.

### Feedback layer

- model-provider interface;
- prompt construction;
- response validation;
- output-length limits;
- retry and error handling;
- provider-specific adapters.

### User interface layer

- Teacher mode;
- Student mode;
- preview mode;
- accessibility behaviour;
- tutorial selection.

### Persistence layer

- local filesystem implementation;
- optional Hugging Face Dataset implementation;
- future database implementation;
- import/export backup.

### Analytics layer

- disabled by default;
- aggregate and anonymised when enabled;
- no dependency on analytics for core tutorial operation.

No interface layer should directly call a specific model provider or storage provider. It should call a documented internal service interface.

## 9. Configuration and Secrets

All environment-specific values must be supplied through environment variables or configuration files excluded from version control.

Provide `.env.example` containing placeholders such as:

```text
LLM_PROVIDER=
LLM_API_KEY=
LLM_MODEL=
TUTORIAL_STORAGE=local
HF_DATASET_REPO=
HF_TOKEN=
APP_BASE_URL=
```

Requirements:

- the application should start in a demonstration mode without paid credentials;
- missing optional configuration should produce a useful message;
- secrets must never appear in tutorial JSON;
- model selection must not be embedded in academic content;
- development, test, and production configurations must be separable.

## 10. Testing Strategy

Independence requires automated tests before extraction.

### Unit tests

- schema validation;
- question/answer matching;
- `.qmd` parsing;
- prompt construction;
- configuration loading;
- storage adapters;
- output filtering.

### Integration tests

- create, edit, save, reload, and export a tutorial;
- import paired `.qmd` files;
- run Student mode using a mocked model;
- verify indicative answers are not sent or exposed prematurely;
- verify operation without the parent repository.

### Regression fixtures

Include anonymised example tutorials covering:

- conceptual questions;
- mathematical questions;
- multi-part questions;
- Markdown tables;
- LaTeX equations;
- reading-based questions;
- alternative valid answers.

### Extraction test

CI must copy or check out only the `ai-assisted-tutorials/` directory into a clean temporary environment and then:

1. install dependencies;
2. validate example tutorials;
3. run all tests;
4. start the application;
5. perform a health check.

This is the most important technical proof that the module is truly independent.

## 11. Documentation Package

The standalone subproject should include:

- a five-minute quick start;
- installation instructions;
- local development instructions;
- academic authoring guide;
- completed example tutorial;
- JSON schema reference;
- deployment guide;
- iframe/LMS embedding guide;
- model-provider configuration guide;
- accessibility statement;
- privacy and governance guide;
- testing checklist;
- troubleshooting guide;
- upgrade and schema-migration guide.

Documentation must not assume familiarity with the Monetary Economics repository.

## 12. Governance and Accessibility

Before institutional use:

- state clearly that feedback is AI-generated;
- describe its limitations;
- identify the human escalation route;
- specify whether data are stored and for how long;
- minimise collection of names, IDs, and free-text logs;
- make analytics optional;
- prohibit high-stakes use without separate validation;
- document model and prompt changes;
- provide keyboard navigation;
- use labelled controls and logical heading structure;
- test screen-reader behaviour;
- avoid relying only on colour to convey feedback;
- support readable equations and responsive layouts.

## 13. Migration from the Current Repository

Migration should be incremental to avoid breaking the working course.

### Phase A: Document and freeze the boundary

- Treat `hf-spaces/tutorial-builder/` as the current implementation.
- Record its current features and known limitations.
- Identify all references to parent-level files.
- Identify all hard-coded course names, topic conventions, URLs, and secrets.
- Do not move code yet.

### Phase B: Add tests around existing behaviour

- Add schema tests for current tutorial JSON.
- Add fixtures based on copies of course tutorials.
- Mock all external AI calls.
- Test Teacher mode and Student mode.
- Add a clean-directory startup test.

### Phase C: Establish the independent package

- Add application packaging and an independent dependency file.
- Add `.env.example`.
- Add local example tutorials.
- Add the canonical schema.
- Make all paths relative to the subproject root or supplied configuration.

### Phase D: Decouple course content

- Convert the Monetary Economics tutorials into JSON exports.
- Store reusable examples inside the subproject.
- Keep course-owned tutorial data in the course project if preferred.
- Stop reading parent `topicXquestions.qmd` and `topicXanswers.qmd` at runtime.
- Retain `.qmd` parsing only as an explicit import operation.

### Phase E: Move the application

- Move or refactor the builder into `ai-assisted-tutorials/app/`.
- Preserve a compatibility deployment while the main site is tested.
- Update the iframe only after the new deployment passes smoke tests.
- Do not delete the old implementation until rollback is no longer needed.

### Phase F: Make the main project a consumer

- Keep only course-specific source materials and tutorial exports in the main project.
- Embed the standalone deployed application using its public URL.
- Use stable tutorial IDs rather than filesystem paths.
- Document how the course site can operate if the tutorial application is temporarily unavailable.

### Phase G: Extraction rehearsal

- Copy the subproject into a clean repository.
- run its tests and deployment locally;
- deploy a staging instance;
- load a Monetary Economics tutorial through the public interface;
- verify that both repositories build independently.

### Phase H: Optional repository split

When all extraction criteria pass:

- create a new repository;
- preserve relevant history if useful;
- add its own issue tracker, releases, CI, and deployment;
- replace the directory in the main project with documentation or a Git submodule only if a submodule is genuinely required;
- preferably integrate through released artifacts and URLs rather than Git-level coupling.

## 14. Extraction Acceptance Criteria

The subproject is ready to become a separate repository only when all of the following are true:

- [ ] It has its own README, licence, dependency specification, and configuration example.
- [ ] It installs from a clean environment.
- [ ] It runs without files above its own root directory.
- [ ] It includes at least one non-Monetary-Economics example.
- [ ] It does not contain secrets or absolute paths.
- [ ] It does not assume `topicX` naming.
- [ ] Its tutorial schema is documented and versioned.
- [ ] It has automated unit and integration tests.
- [ ] External AI calls are mockable in tests.
- [ ] Storage providers are optional adapters.
- [ ] The course website builds when the application is absent.
- [ ] The application runs when the course repository is absent.
- [ ] A staging deployment has passed author and student smoke tests.
- [ ] A rollback path has been tested.
- [ ] Privacy, accessibility, and AI disclosure documentation exists.

## 15. Initial Delivery Plan

| Stage | Deliverable | Completion test |
|---|---|---|
| 1 | Boundary and dependency audit | All current couplings are listed |
| 2 | Versioned tutorial schema | Existing tutorial JSON validates or has a migration path |
| 3 | Independent package skeleton | Installation works inside the subproject directory |
| 4 | Importer and templates | A colleague can create JSON from paired `.qmd` files |
| 5 | Refactored application services | UI is independent of model and storage providers |
| 6 | Automated tests | Clean extraction test passes |
| 7 | Academic pilot | Three to five colleagues publish reviewed tutorials |
| 8 | Governance and accessibility review | Institutional checklist is complete |
| 9 | Staging deployment | The course site loads tutorials using stable IDs |
| 10 | Optional repository extraction | Both projects build and deploy independently |

## 16. Pilot Evaluation

Pilot the toolkit with several academics and different tutorial types:

- conceptual discussion;
- quantitative problem solving;
- evidence or reading interpretation;
- diagram-based reasoning;
- policy evaluation.

Collect:

- time required to create a tutorial;
- import and formatting problems;
- AI feedback errors;
- frequency and quality of student revisions;
- tutor observations;
- accessibility problems;
- usefulness of aggregate misconception reporting;
- changes in live tutorial discussion.

The main success measure is not the volume of AI interaction. It is whether students improve their reasoning and whether tutors can use tutorial time more effectively.

## 17. Immediate Next Actions

1. Audit `hf-spaces/tutorial-builder/` for dependencies on the repository root.
2. Document the current JSON structure and create schema version `1.0`.
3. Copy one tutorial into an anonymised test fixture.
4. Add tests before relocating application code.
5. Create the authoring templates and academic design worksheet.
6. Add independent dependency and environment configuration files.
7. Refactor runtime course-file loading into an explicit import operation.
8. Add a clean extraction test to CI.
9. Deploy a staging instance from the independent directory.
10. Update the Monetary Economics site only after the staging application is verified.

## 18. Important Implementation Principle

Do not begin by physically moving files.

First establish stable data contracts, automated tests, configuration boundaries, and a rollback path. Once those exist, moving the application becomes a controlled packaging change rather than a risky rewrite.
