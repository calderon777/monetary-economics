from shiny import App, ui, render, reactive
from groq import Groq
import os
import pathlib
from dotenv import load_dotenv

load_dotenv()

def load_questions_from_qmd():
    """Load question text from topic3questions.qmd for better context."""
    qmd_path = pathlib.Path("topic3questions.qmd")
    if qmd_path.exists():
        try:
            content = qmd_path.read_text(encoding="utf-8")
            return content
        except Exception as e:
            print(f"Warning: Could not load topic3questions.qmd: {e}")
    return None

INDICATIVE_ANSWERS = {
    1: """**Main points of similarity:**

1. Both approaches relate the transaction demand for money positively to nominal GDP.
2. Both can be interpreted using the Cambridge Equation of Exchange as a framework, although the treatment of velocity differs between them.

**Main points of difference:**

1. **Store of value role:** Keynes emphasised the store of value role of money, which is neglected by the Quantity Theory of Money (QTM). The store-of-value role leads to Keynes' Liquidity Preference theory, which relates money demand negatively to the interest rate. It also underlies the precautionary and speculative motives for money demand that Keynes emphasised.

2. **Interest rate determination:** The different approaches to money demand led to different theories of what determines the interest rate. In Classical theory it is determined by equilibrium in the market for loanable funds, while in Keynesian theory it is determined by equilibrium in the money market. However, these two theories can be reconciled using IS-LM analysis.

3. **Full employment and neutrality:** Classics and Keynes took different positions on the ability of markets to generate full employment equilibrium. The Classical belief in dichotomy of the real from the monetary and the neutrality of money is founded on the assumption of wage and price flexibility in all markets. Keynes disagreed with this in two distinct ways: (i) The possibility of a liquidity trap in which an excess demand for money could coexist with an excess supply in the goods market for an indefinite period, despite falling price levels; (ii) Even outside the liquidity trap, because prices adjusted at different rates in different markets, relative prices would not remain unaffected by price movements; hence the principles of dichotomy and neutrality would not hold.""",

    2: """**Three exceptional features:**

(a) The price of money is literally one; this is a direct consequence of its role as unit of account. Unlike other markets where disequilibrium results in changes in the nominal price of the item in question, this is not possible in the market for money.

(b) The supply of money is also unresponsive, as money is exogenously supplied by a sovereign authority (a Central Bank in the modern context).

(c) There are no close substitutes for money in terms of the liquidity services that it provides (although this is less true today than it was in Keynes' time).

**Is this a problem?**

This is not always a problem. Precisely because money is so central in both asset and goods markets, an exogenous increase in the demand for money can lead to collective adjustments in these markets that restore macroeconomic equilibrium. An increase in the demand for money can lead to an increase in the interest rate (inducing a shift back from money to interest-bearing assets) and/or a decrease in the price level (inducing an increase in the demand for goods collectively, and thus a decrease in the demand for money via Walras' Law).

**When it becomes a problem:**

These normal adjustment mechanisms fail to work if the economy is caught in a liquidity trap. In such a situation, economic agents are willing to hold unlimited amounts of money due to its perceived security. Thus neither can the interest rate rise in a liquidity trap, nor can falling prices induce a greater demand for goods.""",

    3: """The liquidity trap is characterised by a situation in which the economy is suffering from low levels of output as well as low interest rates. In such a situation, Keynes argued that economic agents could become unwilling to part with their money (beyond some minimum needed to cover essentials) in exchange either for goods or for other assets. This situation is also known as absolute liquidity preference.

At the individual level, absolute liquidity preference can be justified as a result of agents' uncertainty and pessimism about the future state of the economy. However, when all agents indulge this absolute liquidity preference, the result is precisely the collapse of aggregate demand—and with it economic activity—that agents fear in the first place.

**Why normal price adjustments fail:**

In normal times, an increase in the demand for money might temporarily lead to a decrease in the collective demand for goods at the going market price in each goods market. This would trigger competition between goods' suppliers in each market, leading to a decrease in each good's price, and therefore of the overall price level. This falling price level would induce greater spending on goods—so long as the economy was not in a liquidity trap.

In a liquidity trap, however, falling prices do not induce greater spending precisely because the desire to hoard money is unlimited.

**Why normal interest rate adjustments fail:**

Similarly, because money is also a store of value that competes with interest-bearing stores of value in agents' portfolios, an increase in the demand for money would, in normal times, lead to a collective decrease in the demand for interest-bearing assets. Competition amongst the issuers of such assets would result in a higher interest rate, inducing a shift back by savers into holding such assets and eliminating the excess demand for money.

In a liquidity trap, however, precisely because the desire to hoard money is unlimited, this mechanism also ceases to work."""
}

def get_question_text(num):
    questions = {
        1: "**Question 1: Classical vs. Keynesian Views**\n\nCompare and contrast Classical and Keynesian views on the macroeconomic role of money.",
        2: "**Question 2: Exceptional Features of the Money Market**\n\nWhat features of the market for money make it exceptional in terms of how it reacts if there is a shock to the demand for money? Is this a problem for macroeconomic equilibrium? Why or why not?",
        3: "**Question 3: The Liquidity Trap**\n\nExplain in words alone (without using diagrams) how the normal adjustment mechanisms that allow equilibrium to be restored following an increase in the demand for money, do not work if the economy is in a liquidity trap.",
    }
    return questions.get(num, "")

def create_feedback_prompt(question_num, student_answer, indicative_answer):
    qmd_context = load_questions_from_qmd()
    context_note = ""
    if qmd_context:
        context_note = "\n\nNote: This question is from Topic 3 of EC3014 Monetary Economics."
    
    return f"""You are an expert economics tutor providing feedback on a Monetary Economics question from Topic 3 (Keynes's Theory of Money). Your goal is to help students improve their understanding by providing hints and guidance, NOT complete answers.

QUESTION {question_num}:
{get_question_text(question_num)}

STUDENT'S ANSWER:
{student_answer}

INDICATIVE ANSWER (for your reference only - DO NOT share directly):
{indicative_answer}

TOPIC 3 KEY CONCEPTS:
- Classical vs. Keynesian views on money's role
- Money market exceptionality (price of money, supply rigidity, no substitutes)
- Liquidity preference and store of value
- Liquidity trap and absolute liquidity preference
- Price adjustment mechanisms and their failure in liquidity traps
- Interest rate determination (loanable funds vs. money market equilibrium)

INSTRUCTIONS:
1. Identify what the student got right and acknowledge it
2. If the answer is incomplete or has gaps, provide HINTS to guide them toward the correct reasoning
3. If the answer contains misconceptions, gently point them toward the correct approach
4. For multi-part questions, address each part briefly
5. Encourage them to think about the economic intuition
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
        @media (max-width: 768px) {
            body { padding: 10px; }
            .container-custom { padding: 20px; border-radius: 8px; }
            .header h1 { font-size: 1.8em; }
            .header p { font-size: 1em; }
            .instructions { padding: 15px; }
            .question-card { padding: 15px; }
            .question-text { font-size: 1em; }
            .nav-link { padding: 10px 15px !important; font-size: 0.9em; }
            textarea { font-size: 0.95em; padding: 10px; }
            .btn-primary { width: 100%; padding: 12px !important; }
            .feedback-box { padding: 15px; }
        }
        @media (max-width: 480px) {
            .container-custom { padding: 15px; }
            .header h1 { font-size: 1.5em; }
            .header p { font-size: 0.9em; }
            .question-card { padding: 12px; }
            .nav-link { padding: 8px 12px !important; font-size: 0.85em; }
        }
        </style>
        """),
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
            ui.h1("Topic 3 - Keynes's Theory of Money"),
            ui.p("Interactive questions on liquidity preference, money market dynamics, and the liquidity trap"),
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
