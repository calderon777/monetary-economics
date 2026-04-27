# AI-Persona Debates in the History of Economic Thought: A Ludic Approach to Classical–Keynesian Monetary Controversy

**Author:** Dr Camilo Calderon
**Course context:** EC3014 Monetary Economics
**Submission type:** Economics Network Case Study (Showcase)
**Draft date:** April 2026

---

## 1. Abstract (202 words)

This case study documents a ludic teaching activity for an undergraduate Monetary Economics module in which students interrogate AI personas representing rival schools of economic thought: Walras and Marshall for the Classical tradition, and Keynes and Hicks for the Keynesian tradition. Deployed as a Gradio application on Hugging Face Spaces and embedded in the course's Quarto website, the tool stages a three-round structured debate on money neutrality, liquidity preference, and low-rate monetary policy. The pedagogical novelty lies in student agency: rather than observing a pre-scripted dialogue, students generate the challenge questions that drive each round, pushing each persona to defend mechanisms, not merely conclusions. This note describes the design rationale, the technical implementation (LLM persona prompting, round-specific scaffolding, session hygiene to prevent persistent debate state), and the anticipated and emerging patterns of student engagement. The activity complements—rather than substitutes for—lecture treatment of IS–LM, liquidity preference, and the Pigou critique. It positions itself alongside recent Economics Network entries exploring AI-assisted pedagogy (e.g., Strobel's March 2026 piece on AI-assisted economic game coding) but differentiates by foregrounding history of economic thought, structured adversarial reasoning, and student-generated prompting. Critical reflection addresses hallucination risk, assessment integrity, and the limits of simulated intellectual disagreement.

---

## 2. Full Section Outline

1. **Motivation and context** – Why monetary economics resists pure lecture delivery; why the Classical–Keynesian controversy is an ideal debate substrate; positioning relative to recent Economics Network AI-pedagogy entries.
2. **Activity description** – The debate cast, the three-round structure, the student-question workflow, the classroom choreography.
3. **Pedagogical design rationale** – Active learning, role-play, disciplinary thinking in history of economic thought, student agency through question-generation.
4. **Technical implementation** – Gradio on Hugging Face Spaces, LLM persona prompting architecture, round-specific scaffolds, iframe embedding in a Quarto course site, session hygiene.
5. **Student response and evidence** – Observed engagement patterns; anticipated learning outcomes; indicators to be formally measured (evidence pending).
6. **Critical reflection** – Hallucination and misattribution risk; assessment integrity; inequality of prior knowledge; the "simulated consensus" trap.
7. **Replication guide** – What a colleague needs to redeploy the activity in another module.
8. **Conclusion** – Contribution to AI-assisted active learning in economics.
9. **References** – Works cited (flagged where citation is pending).

---

## 3. Full Article (≈ 2,100 words)

### 3.1 Motivation and Context

Monetary economics is difficult to teach well. The core of the Classical–Keynesian debate is not a matter of competing calculations; it is a matter of competing assumptions about how an economy adjusts when money is part of it. Whether Say's Law survives in a monetary economy, whether liquidity preference collapses the interest-rate channel at low rates, whether the Pigou effect provides a self-correcting exit from a liquidity trap — each question turns on a small number of theoretical commitments whose consequences ramify far and visibly into policy. Lectures handle this reasonably well when students already hold the relevant mental models. They handle it less well when students are meeting these models for the first time and must also situate them historically.

Role-play and debate formats have long been proposed as a remedy for this kind of content, on the grounds that students who must *voice* a position internalise its mechanisms more robustly than students who only *receive* it [citation needed — active-learning literature, e.g., meta-analyses on undergraduate STEM active learning]. What has changed recently is the cost of providing a credible interlocutor. Large language models now make it feasible to stage a live conversation in which a student types a question and receives a persona-consistent, mechanism-level response within seconds. The Economics Network showcase has begun to reflect this shift: Strobel's March 2026 entry from the University of Birmingham described students building classroom economics games with AI-assisted coding, and Kumon's April 2026 entry extended the AI-pedagogy thread further. The activity reported here contributes to that emerging conversation in three specific ways. First, it places *history of economic thought* — often marginal in contemporary undergraduate monetary economics — at the centre of the exercise. Second, it shifts agency to the student: the AI does not ask the questions, the student does. Third, it uses *multi-persona* prompting, so that students confront a within-school as well as a between-school disagreement (Walras is not Marshall; Keynes is not Hicks).

### 3.2 Description of the Activity

The activity is the third topic of EC3014 Monetary Economics and follows two lecture weeks covering classical quantity theory, loanable funds, Keynesian liquidity preference, and the IS–LM framework. It is deployed on the course's Quarto website as an embedded Gradio application. Students open the activity page after completing the assigned reading on Keynes's theory of money; no installation is required.

Four AI personas are available in two teams. Team Classical comprises Walras (general equilibrium, Walras' Law, classical dichotomy, long-run neutrality) and Marshall (Cambridge cash-balance view, money demand and velocity). Team Keynesian comprises Keynes (liquidity preference, the three motives for holding money, the liquidity trap) and Hicks (the IS–LM synthesis and short-run disequilibrium). Students select one of three rounds — *Neutrality and Real Effects*, *Liquidity Preference and Money Demand*, or *Policy at the Zero Lower Bound* — and pose a focused challenge question. Each team responds in character, and the student iterates for two or three rounds.

Rather than issuing the personas a pre-set question list, students generate their own prompts. The activity page provides indicative examples — "If a central bank doubles the money supply overnight, what happens to output, employment, and real wages in the short run versus the long run?"; "At zero interest rates, why can't central banks stimulate the economy further?"; "Can quantitative easing work if the liquidity trap is real?" — but these are framed as starting points, not a script. Students are asked to press on mechanisms, challenge the assumptions each team takes for granted, and then cross-examine for consistency.

The activity is untimed and ungraded in its current form. It is accompanied by a reflection prompt in the course workbook asking students to record which team made stronger assumptions, which acknowledged uncertainty more openly, and how they would combine the two perspectives into their own framework.

### 3.3 Pedagogical Design Rationale

The design rests on three overlapping pedagogical commitments.

The first is active learning in the conventional sense: students must produce output (a well-formed challenge question) before they can consume output (the personas' response). The literature on active learning in economics has repeatedly reported gains from even modest shifts away from transmissive delivery [citation needed — active-learning in economics literature]. The incremental design cost of this activity is low because the "live interlocutor" problem — the bottleneck in traditional role-play, which requires a prepared instructor and a receptive classroom culture — is absorbed by the model.

The second commitment is to *disciplinary thinking in the history of economic thought*. Undergraduate monetary economics modules often compress the Classical–Keynesian controversy into a stylised comparison that erases within-school disagreement. By separating Walras from Marshall and Keynes from Hicks, the activity forces students to notice that a "Classical" position on money neutrality is not monolithic (Walrasian general equilibrium and Marshall's cash-balance framing reach similar conclusions from different premises), and that a "Keynesian" position is not monolithic either (Hicks's IS–LM synthesis tames Keynes's General Theory in ways that Keynes himself arguably resisted). This is the kind of textured understanding that undergraduates rarely reach through lecture alone.

The third commitment is *student agency through prompting*. In many AI-pedagogy deployments, the student is positioned as the audience for an AI performance. Here, the student is positioned as the debate moderator: the quality of the session is bounded above by the quality of the student's questions. This mirrors the structure of genuine scholarly argument and turns "prompt engineering" into a quietly assessable disciplinary skill.

### 3.4 Technical Implementation

The application is built with Gradio and hosted on Hugging Face Spaces at a stable URL, then embedded via iframe in the course's Quarto website. The choice of stack is deliberate. Gradio is lightweight, free to host at the scale of a single module, requires no server administration from the instructor, and renders cleanly inside an iframe without framework conflicts.

The persona architecture is built around a small number of system prompts — one per persona — each of which fixes (a) the economist's theoretical commitments in the language they would plausibly have used, (b) the concepts they are expected to deploy, and (c) explicit constraints against breaking character or endorsing anachronistic positions. The round selection controls an additional scaffolding prompt that narrows each persona's focus to the round's topic (neutrality, liquidity preference, or low-rate policy). This two-layer structure — *persona prompt × round prompt* — keeps responses on-topic without collapsing the within-school distinctions.

Two implementation details are worth flagging for would-be replicators. First, Hugging Face Spaces iframes can cache conversational state across page loads; without intervention, a student loading the page can inherit the previous student's debate. The course site therefore ships with a small JavaScript block that clears relevant local-storage keys and forces an iframe cache-buster on each page load. Second, the persona prompts are deliberately terse. Long persona prompts tend to collapse into generic "here is what an economist might say" output; shorter, more pointed prompts yield more idiosyncratic — and therefore more useful — disagreement.

The cost profile is modest. At the class size of a single undergraduate module, the activity has run within the Hugging Face Spaces free tier. At larger scale, the main constraint is API cost per turn; the round structure (at most three rounds per student per session) keeps this bounded.

### 3.5 Student Response and Evidence

Formal evaluation is ongoing; what follows should be read as *observed patterns* in early deployment, not as claims supported by a completed study (evidence pending).

Three patterns are visible so far. First, students spend longer on the liquidity-preference round than on either of the other two. A plausible reading is that liquidity preference is the least intuitive of the three topics; a less charitable reading is that the personas disagree most visibly on this round, which is simply more entertaining. Disentangling these will require either a think-aloud protocol or a short post-activity survey [citation needed — evidence pending].

Second, the quality of student questions improves within a single session. Early questions tend to ask for conclusions ("Does QE work?"); later questions tend to ask for mechanisms ("Through which channel does QE operate if the liquidity trap binds, and how does your answer differ from Keynes's?"). This is encouraging because mechanism-level questioning is the transferable skill the activity is designed to cultivate.

Third, students who struggle with the activity tend to struggle at the question-generation step, not at the comprehension step. This is a pedagogically useful signal: it suggests that the bottleneck for these students is not reading the personas' answers but framing a productive challenge. In response, the reflection prompt now includes a scaffolded "question-ladder" exercise to be completed before engaging the personas.

Formal outcome measurement is planned for the next cohort. The intended indicators are pre/post conceptual questions on money neutrality and the liquidity trap, an assessed short essay in which students reconstruct one within-school disagreement (e.g., Keynes vs Hicks on the interpretation of the General Theory), and an end-of-module survey on the activity's perceived usefulness. Until those data are collected, claims about learning gains should be read as hypothesised rather than demonstrated.

### 3.6 Critical Reflection

Four risks deserve explicit acknowledgement.

*Hallucination and misattribution.* The personas are not faithful reconstructions of their historical counterparts; they are LLMs prompted to approximate them. On well-documented positions (Walras' Law, the three motives, the liquidity trap), the approximation is reasonable. On contested or fine-grained questions, the personas can produce confident statements that no careful historian of thought would endorse. Students are told this explicitly in the activity preamble; a residual concern is that the telling is not always absorbed. A productive follow-up is to require students to verify one claim from each persona against a primary source from the reading list.

*Assessment integrity.* The activity is currently formative. Any move to summative assessment must confront the fact that students can use the same tooling to generate the essays we would ask them to write. The answer is to assess the question-generation step and the reflection, not the transcript — but this will require redesign of the marking rubric.

*Inequality of prior preparation.* Students who arrive having done the reading extract much more from the personas than students who have not, because they can recognise when a persona is paraphrasing a canonical argument versus when it is drifting. This is a general feature of active-learning activities, but the speed of the AI responses amplifies the gap: weak students can "finish" quickly without noticing that they have not learned anything.

*The simulated-consensus trap.* LLMs are trained to be agreeable and to synthesise. Without pointed prompting, two personas from opposed schools can converge on an anodyne middle position ("both sides make important points") that resembles neither Classical nor Keynesian thought. The round prompts partially mitigate this, but it remains the most fragile element of the design.

### 3.7 Replication

A colleague wishing to redeploy the activity needs: a Hugging Face account (free tier suffices for typical class sizes); a Gradio application exposing four persona endpoints and one round selector; a small JavaScript cache-busting block if embedding in a Quarto or other static site; and a set of persona and round prompts calibrated to the module's specific reading list. The persona and round prompts used here are available on request and are intended to be adapted rather than copied verbatim.

### 3.8 Conclusion

The contribution of this activity is modest and specific. It does not claim that AI personas replace lectures, seminars, or primary reading. It claims only that, at marginal cost, they provide a rehearsal space in which students can test their own questions against the two most important schools of thought in monetary economics — and that the act of generating those questions is itself where the learning lives. As AI-pedagogy entries accumulate in the Economics Network showcase, the question is no longer *whether* to use these tools but *which* parts of economics education they serve well. History of economic thought, with its premium on mechanism and disagreement, is one such part.

---

## 4. References (pending / indicative)

The following references are either drawn from the course's own lecture materials (verified) or marked as *citation needed* where the claim would require support from a literature the author should verify before submission.

**Verified primary / secondary sources (from lecture materials):**

- Keynes, J. M. (1936). *The General Theory of Employment, Interest, and Money.*
- Hicks, J. R. (1937). "Mr. Keynes and the Classics: A Suggested Interpretation." *Econometrica.*
- Walras, L. (1874). *Éléments d'économie politique pure.*
- Pigou, A. C. (1943). "The Classical Stationary State." *Economic Journal.*
- Patinkin, D. (1956). *Money, Interest, and Prices.*

**Economics Network showcase comparators (user-confirmed):**

- Strobel, F. (March 2026). "Building Classroom Economics Games with AI-Assisted Coding," University of Birmingham — Economics Network Showcase. *[Verify exact title and URL before submission.]*
- Kumon, Y. (April 2026). Economics Network Showcase entry on AI pedagogy. *[Verify exact title, author affiliation, and URL before submission.]*

**Citations needed (do not invent — author to source):**

- Active-learning meta-analysis in undergraduate STEM / economics (e.g., Freeman et al.'s 2014 PNAS meta-analysis is the canonical reference; *author to verify and cite*).
- Role-play and simulation pedagogy in economics.
- AI in higher education — responsible-use frameworks and empirical studies of LLMs in tutorial settings.
- History of economic thought teaching literature, especially on within-school pluralism.

---

## 5. Claims / Evidence Table

| # | Claim | Supporting source | Confidence | Needs citation |
|---|-------|-------------------|------------|----------------|
| 1 | Classical economists (Walras, Marshall) held that money is neutral in the long run via the classical dichotomy. | Lecture notes (topic3reading.qmd); Walras (1874); Lewis & Mizen (2000) | High | No — already referenced in course materials |
| 2 | Keynes introduced three motives for holding money: transactions, precautionary, and speculative. | Keynes (1936); lecture notes | High | No |
| 3 | Hicks (1937) formalised Keynes via IS–LM and is understood by many historians as partially "taming" the General Theory. | Hicks (1937); lecture notes reference the IS–LM synthesis | Medium | Yes — the "taming" interpretation needs a specific HET citation (e.g., Leijonhufvud or similar) |
| 4 | The Pigou (1943) / Patinkin (1956) real-balance critique offers a potential market-based exit from the liquidity trap. | Pigou (1943); Patinkin (1956); lecture notes | High | No |
| 5 | Active learning improves undergraduate outcomes in economics and related disciplines relative to pure transmissive delivery. | — | Medium | Yes — needs active-learning meta-analysis (e.g., Freeman et al. 2014 is canonical; author to verify) |
| 6 | Role-play and debate formats are effective in teaching contested theoretical frameworks. | — | Medium | Yes — needs economics-pedagogy or HET-teaching citation |
| 7 | LLMs can plausibly sustain persona-consistent dialogue sufficient for undergraduate pedagogical use. | — | Medium | Yes — needs AI-in-education empirical citation; author should not overclaim |
| 8 | The Economics Network has recently published AI-pedagogy case studies (Strobel, March 2026; Kumon, April 2026). | User-provided context | Medium | Yes — verify exact titles, authors, and URLs before submission |
| 9 | Students spend longer on the liquidity-preference round than on neutrality or low-rate policy rounds. | Author's classroom observation | Low | N/A — marked as "evidence pending"; not to be submitted as supported claim until systematically measured |
| 10 | Question quality within a single student session progresses from conclusion-seeking to mechanism-seeking. | Author's classroom observation | Low | N/A — evidence pending |
| 11 | LLM personas risk producing a "simulated-consensus" middle position when not strongly prompted. | General practitioner knowledge of LLM behaviour | Medium | Yes — citation to an AI-alignment or LLM-behaviour piece would strengthen the claim; author should not fabricate |
| 12 | Gradio on Hugging Face Spaces is technically adequate for single-module classroom deployment. | Author's implementation experience | High | No — operational claim, supportable by the author's own deployment |
| 13 | Iframe-embedded Hugging Face Spaces can leak conversational state across page loads without cache-busting. | Author's implementation experience; visible in code | High | No — technical claim, supportable by the author's own code |
| 14 | Students who struggle with the activity tend to struggle at question-generation, not at comprehension. | Author's classroom observation | Low | N/A — evidence pending |
| 15 | History of economic thought is often marginal in contemporary undergraduate monetary economics curricula. | Common impression among HET educators | Medium | Yes — a curriculum-survey citation would strengthen this; author to source |

---

## 6. Reviewer-Style Critique

The following is written as an imagined referee report for an Economics Network editor.

**Overall judgement.** The case study is timely, well-situated relative to recent showcase entries, and describes a genuine pedagogical intervention with replicable technical detail. I recommend *revise and resubmit* rather than outright acceptance. The principal weaknesses are around evidence of learning outcomes, the specificity of the citation scaffolding, and the balance between description and critical reflection.

**Weaknesses and risks.**

1. *Thin evidence base.* The article repeatedly qualifies outcome claims with "evidence pending" and "anticipated." This honesty is welcome, but it also means the piece is currently closer to an *implementation report* than a *case study of learning*. The Economics Network showcase has historically accepted both, but reviewers will ask for at least one concrete piece of student-facing evidence: an anonymised transcript, a sample student reflection, a pre/post item, or a short end-of-module survey result. Without any such artefact, the contribution reads as a proposal.

2. *Citation scaffolding is incomplete.* The case study flags multiple places where citations are needed (active-learning literature, AI-in-education, role-play pedagogy, HET curriculum). For submission to a pedagogy-focused outlet, at least the active-learning meta-analysis and one role-play-in-economics citation should be sourced and verified. The draft should not be submitted with bracketed "[citation needed]" markers.

3. *Risk discussion is honest but under-developed.* The four risks identified in Section 3.6 (hallucination, assessment integrity, inequality of preparation, simulated consensus) are the right four risks. Each currently receives one paragraph. The simulated-consensus risk in particular deserves a worked example — a case where two personas converged inappropriately, and what was done to mitigate it. Without the example, the risk discussion can read as *pro forma.*

4. *Under-specified persona evaluation.* The article claims the personas produce "reasonable" approximations of their historical counterparts on well-documented positions. A stronger version of the article would include at least one instance of faithful reproduction and one instance of drift, with a short commentary on what distinguishes the two. This would address the hallucination concern substantively rather than rhetorically.

5. *Within-school disagreement is announced but not demonstrated.* Section 3.3 claims that the activity exposes students to within-school disagreement (Walras vs Marshall; Keynes vs Hicks). This is one of the piece's most novel claims, and it is not illustrated. A half-page worked example of a Keynes–Hicks within-school disagreement — perhaps on the interpretation of the liquidity trap — would materially strengthen the contribution.

6. *Comparator framing is slightly defensive.* The positioning relative to Strobel (March 2026) is handled reasonably, but the Kumon (April 2026) comparator is named rather than engaged with. Either engage substantively or drop.

7. *The "student agency" claim bears unexamined weight.* The article repeatedly emphasises that students generate the questions. This is true operationally, but students who follow the suggested question list closely are not really generating anything; they are choosing. A more honest framing would distinguish *question generation* from *question selection* and discuss how the activity design pushes students from the latter toward the former.

**Concrete revision suggestions.**

- Replace all `[citation needed]` markers with verified citations or remove the claim.
- Add one anonymised student artefact (transcript excerpt, reflection, or survey item) even if preliminary.
- Add a worked example (≈ 150 words) of a within-school disagreement elicited by the activity.
- Add a worked example (≈ 150 words) of a simulated-consensus failure and the prompt-engineering response.
- Trim Section 3.2 by ≈ 50 words to make room; the description of the round structure repeats content visible on the course website and can be compressed.
- Soften the "student agency" framing in Section 3.3 to distinguish generation from selection.
- Add a one-paragraph "Limitations" coda before Section 3.8 so that the risks section and the conclusion are not separated by replication notes.
- In the references section, verify the Strobel and Kumon entries (exact titles and URLs) before submission; current provenance is user-reported rather than confirmed.

**Items not to change.**

- The tone is appropriately hedged and non-hyped, which is the correct register for this outlet.
- The technical implementation section (Section 3.4) is exactly the right level of detail for replication.
- The decision to foreground history of economic thought is distinctive and should be kept prominent.

---

*End of draft package.*
