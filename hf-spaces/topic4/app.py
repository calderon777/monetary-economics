from shiny import App, ui, render, reactive
from groq import Groq
import os
import pathlib
from dotenv import load_dotenv

load_dotenv()

def load_questions_from_qmd():
    qmd_path = pathlib.Path("topic4questions.qmd")
    if qmd_path.exists():
        try:
            content = qmd_path.read_text(encoding="utf-8")
            return content
        except Exception as e:
            print(f"Warning: Could not load topic4questions.qmd: {e}")
    return None

INDICATIVE_ANSWERS = {
    1: """Long-run equilibrium: θ = 4, N = 400, Y = 3200, P₀ = 5, W₀ = 20. When M increases to 48000: P₁ = 7.5, W₁ = 30, but θ, N, Y unchanged. Model exhibits dichotomy and neutrality—real variables determined by production and labour preferences only; money supply affects only nominal variables proportionally in long run.""",
    2: """Short-run with money illusion: W' ≈ 24.49, N' ≈ 489.8, Y' ≈ 3545.7, P' ≈ 6.76, θ' ≈ 3.62. Workers observe higher nominal wage but perceive lower inflation than actual, so supply more labour. Real wage falls below natural level (θ' < θ), employment and output expand. Shows how money illusion creates short-run monetary non-neutrality that reverses in long run as expectations adjust.""",
    3: """Initial: π = 2%, i = 4%. When gM increases to 6%: SR – output growth rises temporarily (~1.5%), inflation lags increase in money growth, real interest rates fall. LR – gY returns to 1%, π settles at 5%, i rises to 7%, r returns to 2%. Demonstrates Phillips curve trade-off in SR but vertical long-run Phillips curve; monetary policy has temporary real effects because inflation expectations lag.""",
}

def get_question_text(num):
    questions = {
        1: """**Question 1: Monetarist Model of the Labour Market**

Consider the monetarist model with labour supply $N^S = 100\\theta$, labour demand $N^D = \\frac{6400}{\\theta^2}$, production function $Y = 160\\sqrt{N}$, and QTM $M = 2PY$. Verify labour demand consistency with production function. Find equilibrium values of θ and N. With M₀ = 32000, solve for P₀ and W₀. If M increases to 48000, will θ, N, Y be affected in long run? Solve for P₁ and W₁. Does the model exhibit dichotomy and neutrality of money?""",
        2: """**Question 2: Short-Run Effects with Money Illusion**

Starting from M₀ = 32000, money supply increases to M₁ = 48000. But workers cannot perceive the price increase and temporarily use the original price P₀ as reference. Labour supply becomes $N^S = 100\\frac{W}{P_0}$. Derive the relationship $P' = \\frac{\\sqrt{80}(W')^{3/2}{160}$ from labour market equilibrium. Derive $P' = \\frac{150}{\\sqrt{20W'}$ from output and QTM. Solve for W', Y', P' and θ'. Verify labour market equilibrium. How does this illustrate Friedman's short- versus long-run monetary policy effects?""",
        3: """**Question 3: Dynamic QTM and Monetary Growth**

Given gY = 1% per year, gM = 3% (initially), long-run r = 2%. Using dynamic QTM and Fisher equation, find π and i. Now suppose gM accelerates to 6%. How does this affect (i) growth of output, (ii) inflation rate, (iii) nominal interest rate, (iv) real interest rate in both short run and long run? Explain and illustrate on diagrams showing time paths of these variables.""",
    }
    return questions.get(num, "")

def create_feedback_prompt(question_num, student_answer, indicative_answer):
    qmd_context = load_questions_from_qmd()
    context_note = ""
    if qmd_context:
        context_note = "\n\nNote: This question is from Topic 4 - Friedman's Monetarism in EC3014 Monetary Economics."
    
    topic_concepts = {
        1: "monetarist model, labour market equilibrium, production function, QTM, dichotomy of real and nominal variables, neutrality of money",
        2: "money illusion, short-run labour supply, real vs nominal wages, Friedman's short-run monetary effects, expectations lag",
        3: "dynamic QTM, Fisher equation, monetary growth, inflation lag, Phillips curve, expectations-augmented expectations, short-run vs long-run neutrality",
    }
    
    key_concepts = topic_concepts.get(question_num, "Topic 4 concepts")
    
    return f"""You are an expert economics tutor providing feedback on a Monetary Economics question from Topic 4: Friedman's Monetarism. Your goal is to help students improve their understanding by providing hints and guidance, NOT complete answers.

Key concepts for this question: {key_concepts}

QUESTION {question_num}:
{get_question_text(question_num)}

STUDENT'S ANSWER:
{student_answer}

INDICATIVE ANSWER (for your reference only - DO NOT share directly):
{indicative_answer}

INSTRUCTIONS:
1. Identify what the student got right and acknowledge it
2. If the answer is incomplete or has gaps, provide HINTS to guide them toward the correct reasoning
3. For multi-part questions, address each part briefly
4. If misconceptions exist, gently point toward the correct approach
5. Connect to the key economic concepts listed above
6. Encourage them to verify calculations and economic intuition
7. Keep feedback concise (200-250 words max)
8. Be encouraging and constructive

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
        ui.HTML('''
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
        .answer-section,
        .answer-section .shiny-input-container,
        .answer-section .form-control,
        .answer-section textarea,
        .answer-section textarea.form-control {
            width: 100% !important;
            max-width: 100% !important;
            min-width: 100% !important;
        }
        .answer-section textarea,
        .answer-section textarea.form-control {
            width: 100% !important;
            max-width: 100% !important;
            min-width: 100% !important;
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
        @media (max-width: 768px) {
            body { padding: 10px; }
            .container-custom { padding: 20px; }
            .header h1 { font-size: 1.8em; }
            .question-card { padding: 15px; }
        }
        </style>
        '''),
        ui.tags.script("""
        window.MathJax = {
          tex: {
            inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
            displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
            processEscapes: true
          },
          svg: { fontCache: 'global' }
        };
        """),
        ui.tags.script(src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"),
        ui.tags.script("""
        function renderMath() {
          if (window.MathJax) {
            MathJax.typesetPromise().catch(err => console.error('MathJax error:', err));
          }
        }
        document.addEventListener('DOMContentLoaded', renderMath);
        const observer = new MutationObserver(renderMath);
        observer.observe(document.body, { childList: true, subtree: true });
        """))
    ),
    ui.div(
        ui.div(
            ui.h1("Topic 4 - Friedman's Monetarism"),
            ui.p("Interactive questions on monetarist models, money illusion, and dynamic monetary theory"),
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
            </ol>
            """),
            class_="instructions"
        ),
        ui.navset_tab(
            ui.nav_panel(
                "Question 1",
                ui.div(
                    ui.div(ui.markdown(get_question_text(1)), class_="question-text"),
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
                    ui.div(ui.markdown(get_question_text(2)), class_="question-text"),
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
            ui.nav_panel(
                "Question 3",
                ui.div(
                    ui.div(ui.markdown(get_question_text(3)), class_="question-text"),
                    ui.div(
                        ui.tags.label("Your Answer:"),
                        ui.input_text_area("answer3", "", height="400px", placeholder="Type your answer here..."),
                        ui.input_action_button("submit3", "Get AI Feedback", class_="btn-primary"),
                        class_="answer-section"
                    ),
                    ui.output_ui("feedback3"),
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

    @render.ui
    @reactive.event(input.submit3)
    def feedback3():
        feedback = get_ai_feedback(3, input.answer3())
        return ui.div(
            ui.div(
                ui.h3("AI Tutor Feedback", style="margin-top: 0; color: #2e7d32;"),
                ui.markdown(feedback),
                class_="feedback-box"
            )
        )

app = App(app_ui, server)
