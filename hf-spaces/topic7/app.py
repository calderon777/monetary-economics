from shiny import App, ui, render, reactive
from groq import Groq
import os
import pathlib
from dotenv import load_dotenv

load_dotenv()

def load_questions_from_qmd():
    qmd_path = pathlib.Path("topic7questions.qmd")
    if qmd_path.exists():
        try:
            content = qmd_path.read_text(encoding="utf-8")
            return content
        except Exception as e:
            print(f"Warning: Could not load topic7questions.qmd: {e}")
    return None

INDICATIVE_ANSWERS = {
    1: """Two key problems: (i) Central banks control only the monetary base (M₀), but broader money aggregates (M₁, M₂) include demand deposits created by commercial banks. The money multiplier depends on bank reserve decisions and public preferences, which are unstable. (ii) Money demand is not stable—financial innovation (money market funds, sweep accounts), payment technology changes (credit cards, digital payments), and deregulation shifted money demand unpredictably. Without stable money demand, targeting money growth didn't reliably control inflation. These problems motivated shift to interest rate targeting.""",
    2: """Three key problems: (i) Deflation risk—inflation fluctuates around target; with zero target, deflation risk is high and one-sided. Deflation is self-reinforcing and triggers zero lower bound, making monetary policy ineffective. (ii) Interest rate constraint—with 2% target, CB has buffer before hitting zero bound; with zero target, little room to cut rates during recessions. (iii) Wage adjustment mechanism—positive inflation allows real wage falls without nominal cuts. Workers resist nominal wage cuts; moderate inflation (e.g. 2%) erodes real wages naturally, helping labour markets clear during downturns. Zero inflation requires explicit wage cuts, prolonging unemployment.""",
    3: """Policy rate is overnight lending rate between CB and banks; primary instrument for most central banks. Three transmission channels: (i) Credit channel (indirect)—rate ↑ → bank lending rates ↑ → investment/spending ↓ → labour/goods demand ↓ → wages/prices ↓; (ii) Expectations channel (direct)—rate ↑ → CB signals π will ↓ → wage/price setters expect lower inflation → moderate wage/price setting → π↓ (faster); (iii) Exchange rate channel—rate ↑ → foreign capital inflows → currency appreciates → import prices ↓ → π↓. See diagram for all three channels operating simultaneously.""",
}

def get_question_text(num):
    questions = {
        1: """**Question 1: Problems Leading to Abandonment of Money Supply Targeting**

What problems led major central banks to abandon direct control of the money supply as the primary instrument of monetary policy? Explain.""",
        2: """**Question 2: Why Zero Inflation is Undesirable**

Why is zero inflation considered to be an undesirable target for monetary policy? Explain all the relevant points in this argument.""",
        3: """**Question 3: The Policy Interest Rate and Transmission Channels**

What instrument is normally used to keep inflation close to its target and through what channels does it work in achieving this task? Discuss with the help of a diagram.""",
    }
    return questions.get(num, "")

def create_feedback_prompt(question_num, student_answer, indicative_answer):
    qmd_context = load_questions_from_qmd()
    context_note = ""
    if qmd_context:
        context_note = "\n\nNote: This question is from Topic 7 - Monetary Policy Instruments and Inflation Targeting in EC3014 Monetary Economics."
    
    topic_concepts = {
        1: "monetary base, money supply, money multiplier, financial innovation, money demand stability, commercial banks, interest rate targeting",
        2: "zero inflation, deflation risk, zero lower bound, nominal interest rates, wage rigidity, real wages, labour market adjustment",
        3: "policy interest rate, transmission channels, credit channel, expectations channel, exchange rate channel, inflation dynamics",
    }
    
    key_concepts = topic_concepts.get(question_num, "Topic 7 concepts")
    
    return f"""You are an expert economics tutor providing feedback on a Monetary Economics question from Topic 7: Monetary Policy Instruments and Inflation Targeting. Your goal is to help students improve their understanding by providing hints and guidance, NOT complete answers.

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
6. For Question 3, encourage them to think about how all three channels work together
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
        return f"Error getting feedback: {{str(e)}}. Make sure your GROQ_API_KEY environment variable is set correctly."

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
        .header {{
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 20px;
        }
        .header h1 {{
            color: #333;
            font-size: 2.5em;
            margin: 0 0 10px 0;
            font-weight: 600;
        }
        .header p {{
            color: #666;
            font-size: 1.1em;
            margin: 0;
        }
        .instructions {{
            background: #f0f4ff;
            border-left: 4px solid #667eea;
            padding: 20px;
            border-radius: 6px;
            margin-bottom: 30px;
        }
        .instructions h3 {{
            color: #333;
            margin-top: 0;
        }
        .instructions ol {{
            color: #555;
            line-height: 1.8;
        }
        .nav-tabs {{
            border-bottom: 2px solid #e0e0e0 !important;
            margin-bottom: 25px;
        }
        .nav-link {{
            color: #666 !important;
            font-weight: 500;
            padding: 12px 20px !important;
            border: none !important;
            border-bottom: 3px solid transparent !important;
            transition: all 0.3s ease;
        }
        .nav-link:hover {{
            color: #667eea !important;
            border-bottom-color: #667eea !important;
        }
        .nav-link.active {{
            color: #667eea !important;
            border-bottom-color: #667eea !important;
            background: transparent !important;
        }
        .question-card {{
            background: #fafafa;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 20px;
            width: 100%;
        }
        .question-text {{
            color: #333;
            font-size: 1.1em;
            line-height: 1.6;
            margin-bottom: 15px;
            white-space: pre-line;
        }
        .answer-section {{
            margin-top: 20px;
            width: 100%;
        }
        .answer-section label {{
            display: block;
            color: #555;
            font-weight: 600;
            margin-bottom: 10px;
        }
        .shiny-input-container {{
            width: 100% !important;
        }
        textarea,
        textarea.form-control {{
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
        textarea:focus {{
            border-color: #667eea !important;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            outline: none;
        }
        .btn-primary {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            border: none !important;
            color: white !important;
            font-weight: 600;
            padding: 12px 30px !important;
            border-radius: 6px;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            margin-top: 15px;
        }
        .btn-primary:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4) !important;
        }
        .feedback-box {{
            margin-top: 20px;
            padding: 20px;
            background: #e8f5e9 !important;
            border-left: 4px solid #4caf50 !important;
            border-radius: 6px;
            border: 1px solid #c8e6c9 !important;
        }
        .feedback-box h3 {{
            color: #2e7d32;
            margin: 0 0 10px 0;
        }
        .feedback-box p, .feedback-box li {{
            color: #333;
            line-height: 1.6;
        }
        @media (max-width: 768px) {{
            body {{ padding: 10px; }}
            .container-custom {{ padding: 20px; }}
            .header h1 {{ font-size: 1.8em; }}
            .question-card {{ padding: 15px; }}
        }}
        </style>
        '''),
        ui.tags.script(src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"),
    ),
    ui.div(
        ui.div(
            ui.h1("Topic 7 - Monetary Policy Instruments and Inflation Targeting"),
            ui.p("Interactive questions on policy rates, transmission channels, and inflation targets"),
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
