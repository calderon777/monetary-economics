from shiny import App, ui, render, reactive
from groq import Groq
import os
import pathlib
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Try to load topic1questions.qmd for context
def load_questions_from_qmd():
    """Load question text from topic1questions.qmd for better context."""
    qmd_path = pathlib.Path("topic1questions.qmd")
    if qmd_path.exists():
        try:
            content = qmd_path.read_text(encoding="utf-8")
            # Extract questions from QMD (basic extraction)
            # This is optional; you can also keep hardcoded versions
            return content
        except Exception as e:
            print(f"Warning: Could not load topic1questions.qmd: {e}")
    return None

# Store indicative answers for each question
INDICATIVE_ANSWERS = {
    1: """The Store of Value (SoV) role of money automatically follows from its Medium of Exchange (MoE) role. This is because using money as MoE leads inevitably to a time gap between acquiring money through sale and spending it to buy something else. During this time, money stores the value of what was sold.

However, there is no inevitable link between MoE and Unit of Account (UoA). The need for a UoA can arise even in a non-monetary economy to define prices. While it makes sense for the MoE to also serve as UoA, they are conceptually independent functions.

Examples of UoA without MoE:
- IMF's Special Drawing Right (SDR): A fictitious currency based on a basket of major currencies, used to denominate loans but not freely traded
- European Currency Unit (ECU): Preceded the Euro, used for harmonizing accounts but not an actual medium of exchange""",
    2: """Liquidity is characterized by four key attributes:
(i) Marketability - ease of sale
(ii) Predictability of exchange value - more stable than individual goods
(iii) Reversibility - minimal loss of value between acquisition and sale
(iv) Divisibility - can be used for even the smallest transactions

Whatever serves as the MoE acquires these characteristics by virtue of being universally accepted. However, not any object can become MoE. Physical attributes required include:
(i) Transportability - easy to carry
(ii) Durability - does not physically depreciate
(iii) Inherent divisibility - can be broken into small units
(iv) Universal appeal - not repulsive to users

These objective criteria limit what can serve as effective money.""",
    3: """Alternative mechanisms to the use of a medium of exchange:

1. Middleman/Clearinghouse approach:
In the three-trader example, one trader could accept their least preferred good to facilitate the chain of exchanges. For instance, if Ina accepts Apples from Harriet (her least preferred), she can then trade with Jamal to get Cabbage (her most preferred).

Problem: This requires perfect knowledge of who has what and who wants what. Search and informational frictions make this risky.

2. Multilateral simultaneous trades:
All traders meet at once and exchange cooperatively (Ina gives Bananas to Harriet, who gives Apples to Jamal, who gives Cabbage to Ina - all simultaneously).

Problem: This becomes extremely difficult with many traders and goods. Coordination costs are prohibitive.

Conclusion: The use of a MoE simplifies all these complications and reduces transaction costs significantly."""
}


def get_question_text(num):
    questions = {
        1: "A. Does the Unit of Account (UoA) role of money follow from the Medium of Exchange (MoE) role or is it independent? B. If independent, provide an example of a UoA that is not a widely used MoE.",
        2: "What are the characteristics that underlie liquidity? Can any object acquire these characteristics or are there some physical attributes that must be met?",
        3: "In the example of three agents and three goods, can you think of an alternative to the use of a medium of exchange that might have allowed the three traders to acquire their most preferred good?",
    }
    return questions.get(num, "")


def create_feedback_prompt(question_num, student_answer, indicative_answer):
    qmd_context = load_questions_from_qmd()
    context_note = ""
    if qmd_context:
        context_note = "\n\nNote: This question is from topic1questions.qmd, which is synced to HF Space for reference."
    
    return f"""You are an expert economics tutor providing feedback on a Monetary Economics question from Topic 1. Your goal is to help students improve their analysis and evaluation skills by providing hints and guidance, NOT complete answers.

QUESTION {question_num}:
{get_question_text(question_num)}

STUDENT'S ANSWER:
{student_answer}

INDICATIVE ANSWER (for your reference only - DO NOT share directly):
{indicative_answer}

INSTRUCTIONS:
1. Identify what the student got right and acknowledge it
2. If the answer is incomplete or has gaps, provide HINTS to guide them toward:
   - Key concepts they may have missed
   - Logical connections they should explore
   - Examples they could consider
3. If the answer contains misconceptions, gently point them toward the correct reasoning without giving the answer
4. Encourage critical thinking with probing questions
5. Keep feedback concise (150-200 words max)
6. Be encouraging and constructive

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

        # Use a supported Groq production model
        # Current production models: llama-3.3-70b-versatile, llama-3.1-8b-instant
        # See https://console.groq.com/docs/models for latest available models
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
        .note-link {
            text-align: center;
            color: #999;
            font-size: 0.9em;
            margin-bottom: 20px;
        }
        .note-link a {
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }
        .note-link a:hover {
            text-decoration: underline;
        }
        
        /* Responsive Design for Mobile and Tablets */
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
        """)
    ),
    ui.head_content(
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
        """)
    ),
    ui.div(
        ui.div(
            ui.h1("Topic 1 - Monetary Economics Questions"),
            ui.p("Enhance your understanding of monetary economics with interactive AI-powered feedback"),
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
                        ui.markdown(
                            """**A.** Any object that serves as a medium of exchange (MoE) will also serve as a store of value (SoV). What about the unit of account (UoA) role of money? Does it also follow from the MoE role or is it an independent feature of money?

**B.** If you believe that UoA is independent of MoE, can you provide one example of a UoA that is not itself a widely used MoE?"""
                        ),
                        class_="question-text"
                    ),
                    ui.div(
                        ui.tags.label("Your Answer:"),
                        ui.input_text_area("answer1", "", height="300px", placeholder="Type your answer here..."),
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
                        ui.markdown(
                            """What are the characteristics that underlie liquidity? Can any object acquire these characteristics or are there some physical attributes that must be met?"""
                        ),
                        class_="question-text"
                    ),
                    ui.div(
                        ui.tags.label("Your Answer:"),
                        ui.input_text_area("answer2", "", height="300px", placeholder="Type your answer here..."),
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
                    ui.div(
                        ui.markdown(
                            """In the example of three agents and three goods which is discussed in the lectures, can you think of an alternative to the use of a medium of exchange that might have allowed the three traders to acquire their most preferred good?

**Context:**
- Harriet: 6 Bananas > 3 Apples > 1 Cabbage
- Ina: 1 Cabbage > 6 Bananas > 3 Apples
- Jamal: 3 Apples > 1 Cabbage > 6 Bananas

**See also:** [Three agents and three goods example in the reading](https://camcalderon-monetary-economics-ec3014.netlify.app/topic1reading.html#three-agents-example) for the setup and economic motivation."""
                        ),
                        class_="question-text"
                    ),
                    ui.div(
                        ui.tags.label("Your Answer:"),
                        ui.input_text_area("answer3", "", height="300px", placeholder="Type your answer here..."),
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
