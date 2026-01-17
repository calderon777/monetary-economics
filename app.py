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

        # Use a supported Groq model (mixtral-8x7b-32768 was decommissioned)
        message = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-70b-versatile",
        )

        return message.choices[0].message.content
    except Exception as e:
        return f"Error getting feedback: {str(e)}. Make sure your GROQ_API_KEY environment variable is set correctly."


app_ui = ui.page_fluid(
    ui.h1("Topic 1 - Monetary Economics Questions"),
    ui.markdown(
        """
### How to Use This Tutorial

1. Read each question carefully
2. Type your answer in the text box
3. Click "Get AI Feedback" to receive hints and guidance
4. Revise your answer based on the feedback
5. Repeat until you've fully developed your understanding

**Note:** The full question details are available in [topic1questions.qmd](topic1questions.qmd) or [topic1questions.html](docs/topic1questions.html).
"""
    ),
    ui.navset_tab(
        ui.nav_panel(
            "Question 1",
            ui.markdown(
                """**A.** Any object that serves as a medium of exchange (MoE) will also serve as a store of value (SoV). What about the unit of account (UoA) role of money? Does it also follow from the MoE role or is it an independent feature of money?

**B.** If you believe that UoA is independent of MoE, can you provide one example of a UoA that is not itself a widely used MoE?"""
            ),
            ui.input_text_area("answer1", "Your Answer:", height="150px", placeholder="Type your answer here..."),
            ui.input_action_button("submit1", "Get AI Feedback", class_="btn-primary"),
            ui.output_ui("feedback1"),
        ),
        ui.nav_panel(
            "Question 2",
            ui.markdown(
                """What are the characteristics that underlie liquidity? Can any object acquire these characteristics or are there some physical attributes that must be met?"""
            ),
            ui.input_text_area("answer2", "Your Answer:", height="150px", placeholder="Type your answer here..."),
            ui.input_action_button("submit2", "Get AI Feedback", class_="btn-primary"),
            ui.output_ui("feedback2"),
        ),
        ui.nav_panel(
            "Question 3",
            ui.markdown(
                """In the example of three agents and three goods which is discussed in the lectures, can you think of an alternative to the use of a medium of exchange that might have allowed the three traders to acquire their most preferred good?

**Context:**
- Harriet: 6 Bananas > 3 Apples > 1 Cabbage
- Ina: 1 Cabbage > 6 Bananas > 3 Apples
- Jamal: 3 Apples > 1 Cabbage > 6 Bananas"""
            ),
            ui.input_text_area("answer3", "Your Answer:", height="150px", placeholder="Type your answer here..."),
            ui.input_action_button("submit3", "Get AI Feedback", class_="btn-primary"),
            ui.output_ui("feedback3"),
        ),
    ),
)


def server(input, output, session):
    @render.ui
    @reactive.event(input.submit1)
    def feedback1():
        feedback = get_ai_feedback(1, input.answer1())
        return ui.div(
            ui.markdown(f"### AI Tutor Feedback\n\n{feedback}"),
            style="margin-top: 20px; padding: 15px; background-color: #e8f4f8; border-left: 4px solid #2196F3; border-radius: 4px;",
        )

    @render.ui
    @reactive.event(input.submit2)
    def feedback2():
        feedback = get_ai_feedback(2, input.answer2())
        return ui.div(
            ui.markdown(f"### AI Tutor Feedback\n\n{feedback}"),
            style="margin-top: 20px; padding: 15px; background-color: #e8f4f8; border-left: 4px solid #2196F3; border-radius: 4px;",
        )

    @render.ui
    @reactive.event(input.submit3)
    def feedback3():
        feedback = get_ai_feedback(3, input.answer3())
        return ui.div(
            ui.markdown(f"### AI Tutor Feedback\n\n{feedback}"),
            style="margin-top: 20px; padding: 15px; background-color: #e8f4f8; border-left: 4px solid #2196F3; border-radius: 4px;",
        )


app = App(app_ui, server)
