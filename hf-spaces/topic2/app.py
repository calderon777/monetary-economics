from shiny import App, ui, render, reactive
from groq import Groq
import os
import pathlib
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Try to load topic2questions.qmd for context
def load_questions_from_qmd():
    """Load question text from topic2questions.qmd for better context."""
    qmd_path = pathlib.Path("topic2questions.qmd")
    if qmd_path.exists():
        try:
            content = qmd_path.read_text(encoding="utf-8")
            return content
        except Exception as e:
            print(f"Warning: Could not load topic2questions.qmd: {e}")
    return None

# Store indicative answers for each question (from your handwritten notes)
INDICATIVE_ANSWERS = {
    1: """**(a)** Nominal income: y_N = P_1 s_1 + P_2 s_2

**(b)** Budget constraint: P_1 d_1 + P_2 d_2 = y_N

**(c)** Utility maximisation problem using Lagrangian:
L = d_1^α d_2^(1-α) + λ[y_N - P_1 d_1 - P_2 d_2]

First-order conditions:
∂L/∂d_1 = α(d_2/d_1)^(1-α) - λP_1 = 0
∂L/∂d_2 = (1-α)(d_1/d_2)^α - λP_2 = 0
∂L/∂λ = y_N - P_1 d_1 - P_2 d_2 = 0

**(d)** Combining FOCs yields:
d_1* = α(y_N/P_1)
d_2* = (1-α)(y_N/P_2)

These represent optimal choices (demands).

**(e)** Expanding y_N:
d_1* = α[s_1 + (P_2/P_1)s_2]
d_2* = (1-α)[(P_1/P_2)s_1 + s_2]

If all prices double, the ratios P_1/P_2 and P_2/P_1 are unaffected, so demands remain unchanged. This reflects the homogeneity of demand functions.

**(f)** With s_1=2, s_2=10, P_1=2, P_2=1, α=0.5:
d_1* = 0.5[2 + (1/2)(10)] = 3.5
d_2* = 0.5[(2/1)(2) + 10] = 7

Net purchase:
d_1* - s_1 = 3.5 - 2 = 1.5 (net purchase of good 1)
d_2* - s_2 = 7 - 10 = -3 (net sale of good 2)

Note that net purchase of 1 = net sale of 2 in value terms.""",

    2: """**(a)** Budget constraints:

**Nominal terms:**
Agent A: P_1 d_1^A* + P_2 d_2^A* ≤ P_1 s_1^A + P_2 s_2^A
Agent B: P_1 d_1^B* + P_2 d_2^B* ≤ P_1 s_1^B + P_2 s_2^B

**Real terms (good 1 as numeraire):**
Agent A: d_1^A* + (P_2/P_1)d_2^A* ≤ s_1^A + (P_2/P_1)s_2^A
Agent B: d_1^B* + (P_2/P_1)d_2^B* ≤ s_1^B + (P_2/P_1)s_2^B

where demands are functions of relative price and real income.

**(b)** Market clearing conditions:
Good 1: d_1^A* + d_1^B* = s_1^A + s_1^B → D_1 = S_1
Good 2: d_2^A* + d_2^B* = s_2^A + s_2^B → D_2 = S_2

**(c)** Suppose D_1 = S_1 (good 1 market clears) and budget constraints bind (hold as "=").

Adding both agents' real budget constraints:
d_1^A* + (P_2/P_1)d_2^A* + d_1^B* + (P_2/P_1)d_2^B* = s_1^A + (P_2/P_1)s_2^A + s_1^B + (P_2/P_1)s_2^B

Rearranging:
(d_1^A* + d_1^B*) + (P_2/P_1)(d_2^A* + d_2^B*) = (s_1^A + s_1^B) + (P_2/P_1)(s_2^A + s_2^B)

Since D_1 = S_1, the terms in first brackets cancel:
(P_2/P_1)(d_2^A* + d_2^B*) = (P_2/P_1)(s_2^A + s_2^B)
Therefore: D_2 = S_2

**This establishes Walras' Law**: If n-1 markets clear and all budget constraints bind, the nth market must also clear."""
}


def get_question_text(num):
    questions = {
    1: """**Question 1: Utility Maximization**

Consider a trader with utility function $U = d_1^{\alpha} d_2^{1-\alpha}$ where $d_1$ and $d_2$ are demands for goods 1 and 2, and $\alpha \in (0,1)$. Initial endowment: $s_1, s_2$ units.

(a) Write an expression for her nominal income $y_N$ given prices $P_1$ and $P_2$.
(b) Write her budget constraint.
(c) Write down the utility maximisation problem and derive first-order conditions.
(d) Solve for demands $d_1, d_2$ as functions of $P_1, P_2$, and $y_N$.
(e) Express demands as functions of $P_1, P_2, s_1, s_2$. What happens if all prices double?
(f) Calculate net purchase with $s_1=2, s_2=10, P_1=2, P_2=1, \alpha=0.5$.""",

    2: """**Question 2: General Equilibrium in an Exchange Economy**

Consider 2 traders (A, B) and 2 goods (1, 2) with prices $P_1, P_2$.
Endowments: $s^A = (s_1^A, s_2^A)$, $s^B = (s_1^B, s_2^B)$.

(a) Write each agent's budget constraint in (i) nominal terms and (ii) real terms using good 1 as numeraire.
(b) Write the market clearing condition for each good.
(c) Show that when (i) budget constraints bind and (ii) market 1 clears, then market 2 must also clear. What 'law' is illustrated?"""
    }
    return questions.get(num, "")


def create_feedback_prompt(question_num, student_answer, indicative_answer):
    qmd_context = load_questions_from_qmd()
    context_note = ""
    if qmd_context:
        context_note = "\n\nNote: This question is from Topic 2 - Classical Theory of Money."
    
    return f"""You are an expert economics tutor providing feedback on a Monetary Economics question from Topic 2 (Classical Theory of Money). Your goal is to help students improve their understanding of utility maximization, budget constraints, and general equilibrium by providing hints and guidance, NOT complete answers.

QUESTION {question_num}:
{get_question_text(question_num)}

STUDENT'S ANSWER:
{student_answer}

INDICATIVE ANSWER (for your reference only - DO NOT share directly):
{indicative_answer}

TOPIC 2 KEY CONCEPTS:
- Cobb-Douglas utility functions and optimization
- Budget constraints (nominal vs. real)
- Homogeneity of demand functions
- Walras' Law and general equilibrium
- Relative prices and neutrality

INSTRUCTIONS:
1. Identify what the student got right and acknowledge it
2. If the answer is incomplete or has gaps, provide HINTS to guide them toward:
   - Mathematical setup (Lagrangian, FOCs)
   - Economic interpretation (homogeneity, relative prices)
   - Logical connections they should explore
3. If the answer contains misconceptions, gently point them toward the correct reasoning
4. For multi-part questions, address each part briefly
5. Encourage them to think about the economic intuition behind the math
6. Keep feedback concise (200-250 words max)
7. Be encouraging and constructive

Provide your feedback now:{context_note}"""


def get_ai_feedback(question_num, student_answer):
    if not student_answer.strip():
        return "Please provide an answer to receive feedback."

    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            return "Error: GROQ_API_KEY environment variable not set. Please set your Groq API key."

        client = Groq(api_key=api_key)
        indicative_answer = INDICATIVE_ANSWERS.get(question_num, "")
        prompt = create_feedback_prompt(question_num, student_answer, indicative_answer)

        message = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
        )

        return message.choices[0].message.content
    except Exception as e:
        return f"Error getting feedback: {str(e)}. Make sure your GROQ_API_KEY environment variable is set correctly."


app_ui = ui.page_fluid(
    ui.head_content(
        ui.HTML("""
        <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .shiny-page-container {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            min-height: 100vh;
        }
        .container-custom {
            max-width: 1200px;
            width: 95%;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            padding: 40px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 20px;
        }
        .header h1 {
            color: #333;
            font-size: 2.5em;
            margin: 0 0 10px 0;
            font-weight: 600;
        }
        .header p {
            color: #666;
            font-size: 1.1em;
            margin: 0;
        }
        .instructions {
            background: #f0f4ff;
            border-left: 4px solid #667eea;
            padding: 20px;
            border-radius: 6px;
            margin-bottom: 30px;
        }
        .instructions h3 {
            color: #333;
            margin-top: 0;
        }
        .instructions ol {
            color: #555;
            line-height: 1.8;
        }
        .nav-tabs {
            border-bottom: 2px solid #e0e0e0 !important;
            margin-bottom: 25px;
        }
        .nav-link {
            color: #666 !important;
            font-weight: 500;
            padding: 12px 20px !important;
            border: none !important;
            border-bottom: 3px solid transparent !important;
            transition: all 0.3s ease;
        }
        .nav-link:hover {
            color: #667eea !important;
            border-bottom-color: #667eea !important;
        }
        .nav-link.active {
            color: #667eea !important;
            border-bottom-color: #667eea !important;
            background: transparent !important;
        }
        .question-card {
            background: #fafafa;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 20px;
            width: 100%;
        }
        .question-text {
            color: #333;
            font-size: 1.1em;
            line-height: 1.6;
            margin-bottom: 15px;
            white-space: pre-line;
        }
        .answer-section {
            margin-top: 20px;
            width: 100%;
        }
        .answer-section label {
            display: block;
            color: #555;
            font-weight: 600;
            margin-bottom: 10px;
        }
        .shiny-input-container {
            width: 100% !important;
        }
        textarea,
        textarea.form-control {
            display: block !important;
            width: 100% !important;
            max-width: 100% !important;
            min-width: 100% !important;
            box-sizing: border-box !important;
            padding: 12px !important;
            margin: 0 !important;
            border: 2px solid #e0e0e0 !important;
            border-radius: 6px !important;
            font-family: 'Segoe UI', sans-serif !important;
            font-size: 1em !important;
            resize: vertical !important;
            transition: border-color 0.3s ease !important;
        }
        textarea:focus {
            border-color: #667eea !important;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            outline: none;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            border: none !important;
            color: white !important;
            font-weight: 600;
            padding: 12px 30px !important;
            border-radius: 6px;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            margin-top: 15px;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4) !important;
        }
        .feedback-box {
            margin-top: 20px;
            padding: 20px;
            background: #e8f5e9 !important;
            border-left: 4px solid #4caf50 !important;
            border-radius: 6px;
            border: 1px solid #c8e6c9 !important;
        }
        .feedback-box h3 {
            color: #2e7d32;
            margin: 0 0 10px 0;
        }
        .feedback-box p, .feedback-box li {
            color: #333;
            line-height: 1.6;
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            body {
                padding: 10px;
            }
            .container-custom {
                padding: 20px;
                border-radius: 8px;
            }
            .header h1 {
                font-size: 1.8em;
            }
            .header p {
                font-size: 1em;
            }
            .instructions {
                padding: 15px;
            }
            .question-card {
                padding: 15px;
            }
            .question-text {
                font-size: 1em;
            }
            .nav-link {
                padding: 10px 15px !important;
                font-size: 0.9em;
            }
            textarea {
                font-size: 0.95em;
                padding: 10px;
            }
            .btn-primary {
                width: 100%;
                padding: 12px !important;
            }
            .feedback-box {
                padding: 15px;
            }
        }
        
        @media (max-width: 480px) {
            .container-custom {
                padding: 15px;
            }
            .header h1 {
                font-size: 1.5em;
            }
            .header p {
                font-size: 0.9em;
            }
            .question-card {
                padding: 12px;
            }
            .nav-link {
                padding: 8px 12px !important;
                font-size: 0.85em;
            }
        }
        </style>
        """
        ),
        ui.tags.script(\"\"\"\n        window.MathJax = {\n          tex: {\n            inlineMath: [['$', '$'], ['\\\\\\\\(', '\\\\\\\\)']],\n            displayMath: [['$$', '$$'], ['\\\\\\\\[', '\\\\\\\\]']],\n            processEscapes: true\n          },\n          svg: { fontCache: 'global' }\n        };\n        \"\"\"),\n        ui.tags.script(src=\"https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js\"),\n        ui.tags.script(\"\"\"\n        function renderMath() {\n          if (window.MathJax) {\n            MathJax.typesetPromise().catch(err => console.error('MathJax error:', err));\n          }\n        }\n        document.addEventListener('DOMContentLoaded', renderMath);\n        const observer = new MutationObserver(renderMath);\n        observer.observe(document.body, { childList: true, subtree: true });\n        \"\"\")
    ),
    ui.div(
        ui.div(
            ui.h1("Topic 2 - Classical Theory of Money"),
            ui.p("Interactive questions on utility maximization and general equilibrium"),
            class_="header"
        ),
        ui.div(
            ui.h3("How to Use This Tutorial"),
            ui.HTML("""
            <ol>
                <li>Read each question carefully</li>
                <li>Type your answer in the text box</li>
                <li>Click 'Get AI Feedback' to receive hints and guidance</li>
                <li>Revise your answer based on the feedback</li>
                <li>Repeat until you've fully developed your understanding</li>
            </ol>
            """),
            class_="instructions"
        ),
        ui.navset_tab(
            ui.nav_panel(
                "Question 1",
                ui.div(
                    ui.div(
                        ui.markdown(get_question_text(1)),
                        class_="question-text"
                    ),
                    ui.div(
                        ui.tags.label("Your Answer:"),
                        ui.input_text_area("answer1", "", height="400px", placeholder="Type your answer here..."),
                        ui.input_action_button("submit1", "Get AI Feedback", class_="btn-primary"),
                        class_="answer-section"
                    ),
                    ui.output_ui("feedback1"),
                    class_="question-card"
                )
            ),
            ui.nav_panel(
                "Question 2",
                ui.div(
                    ui.div(
                        ui.markdown(get_question_text(2)),
                        class_="question-text"
                    ),
                    ui.div(
                        ui.tags.label("Your Answer:"),
                        ui.input_text_area("answer2", "", height="400px", placeholder="Type your answer here..."),
                        ui.input_action_button("submit2", "Get AI Feedback", class_="btn-primary"),
                        class_="answer-section"
                    ),
                    ui.output_ui("feedback2"),
                    class_="question-card"
                )
            ),
        ),
        class_="container-custom"
    )
)


def server(input, output, session):
    @render.ui
    @reactive.event(input.submit1)
    def feedback1():
        feedback = get_ai_feedback(1, input.answer1())
        return ui.div(
            ui.div(
                ui.h3("AI Tutor Feedback", style="margin-top: 0; color: #2e7d32;"),
                ui.markdown(feedback),
                class_="feedback-box"
            )
        )

    @render.ui
    @reactive.event(input.submit2)
    def feedback2():
        feedback = get_ai_feedback(2, input.answer2())
        return ui.div(
            ui.div(
                ui.h3("AI Tutor Feedback", style="margin-top: 0; color: #2e7d32;"),
                ui.markdown(feedback),
                class_="feedback-box"
            )
        )


app = App(app_ui, server)
