from shiny import App, ui, render, reactive
from groq import Groq
import os
import edge_tts
import asyncio
import base64
from io import BytesIO
import threading

MODEL_NAME = "llama-3.3-70b-versatile"

SYSTEM_CLASSICAL = (
    "You are the Classical team (Leon Walras + Alfred Marshall). "
    "Speak with one unified voice. Emphasize general equilibrium, Walras' Law, "
    "the classical dichotomy, long-run neutrality, and the Cambridge cash-balance view. "
    "Be EXTREMELY concise: maximum 8-10 sentences. Cut ruthlessly—avoid repetition."
)

SYSTEM_KEYNESIAN = (
    "You are the Keynesian team (John Maynard Keynes + John Hicks). "
    "Speak with one unified voice. Emphasize liquidity preference, money demand motives, "
    "the liquidity trap, and IS-LM interactions with short-run non-neutrality. "
    "Be EXTREMELY concise: maximum 8-10 sentences. Cut ruthlessly—avoid repetition."
)

ROUND_GUIDANCE = {
    "Round 1 - Neutrality": "Focus on long-run neutrality vs short-run real effects.",
    "Round 2 - Liquidity Preference": "Focus on money demand stability vs interest sensitivity.",
    "Round 3 - Policy at Low Rates": "Focus on policy options near the effective lower bound.",
}

# Voice settings for each team - mature British voices with gravitas
CLASSICAL_VOICE = "en-GB-RyanNeural"  # Deeper British male for Walras/Marshall
KEYNESIAN_VOICE = "en-GB-ThomasNeural"  # Mature British male for Keynes/Hicks
MODERATOR_VOICE = "en-GB-SoniaNeural"  # Professional British female for moderator

# Speech parameters for debate-like delivery
SPEECH_RATE = "+5%"  # Slightly faster for debate energy
CLASSICAL_PITCH = "-20Hz"  # Very low pitch for gravitas
KEYNESIAN_PITCH = "-18Hz"  # Also very low but distinguishable
MODERATOR_PITCH = "+0Hz"  # Natural female pitch


async def text_to_speech_async(text: str, voice: str, pitch: str = "+0Hz") -> str:
    """Convert text to speech and return base64-encoded audio."""
    try:
        # edge_tts accepts rate and pitch as parameters
        communicate = edge_tts.Communicate(text, voice, rate=SPEECH_RATE, pitch=pitch)
        audio_data = BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.write(chunk["data"])
        audio_data.seek(0)
        # Encode to base64 for embedding in HTML5 audio
        audio_base64 = base64.b64encode(audio_data.read()).decode('utf-8')
        return audio_base64
    except Exception as e:
        print(f"TTS Error: {e}")
        return ""


def text_to_speech(text: str, voice: str, pitch: str = "+0Hz") -> str:
    """Synchronous wrapper for TTS - handles event loop properly."""
    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running (in Shiny), use a new loop in a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, text_to_speech_async(text, voice, pitch))
                return future.result(timeout=30)  # 30 second timeout
        else:
            # No running loop, safe to use asyncio.run
            return asyncio.run(text_to_speech_async(text, voice, pitch))
    except Exception as e:
        print(f"TTS Wrapper Error: {e}")
        return ""


def build_messages(system_prompt, topic, round_label, history, user_question):
    guidance = ROUND_GUIDANCE.get(round_label, "")
    system = (
        f"{system_prompt}\n"
        f"Topic: {topic}\n"
        f"Round: {round_label}\n"
        f"Round guidance: {guidance}\n"
        "Keep response to 150-180 words (12-15 sentences). Be precise, persuasive, and sharp. Avoid waffle."
    )
    messages = [{"role": "system", "content": system}]
    for turn in history:
        messages.append({"role": "user", "content": turn["user"]})
        messages.append({"role": "assistant", "content": turn["assistant"]})
    messages.append({"role": "user", "content": user_question})
    return messages


def get_ai_response(messages):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "Error: GROQ_API_KEY is not set for this Space."

    client = Groq(api_key=api_key)
    try:
        result = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.4,
            max_tokens=400,
        )
        return result.choices[0].message.content.strip()
    except Exception as e:
        error_msg = str(e)
        if "rate_limit" in error_msg.lower() or "429" in error_msg:
            return "⏳ Rate limit reached. Please wait a few minutes and try again."
        elif "401" in error_msg or "invalid" in error_msg.lower():
            return "🔑 API authentication error. Please check the API key."
        else:
            return f"⚠️ API error: {error_msg[:100]}..."


def get_moderator_analysis(topic, round_label, classical_response, keynesian_response):
    """Get a moderator's analysis of who won the exchange."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "Moderator analysis unavailable."

    client = Groq(api_key=api_key)
    
    moderator_prompt = f"""You are an expert economics moderator scoring this debate exchange.

Topic: {topic}
Round: {round_label}

Classical argument: {classical_response}

Keynesian argument: {keynesian_response}

Score this exchange in 2-3 punchy sentences:
1. Who made the stronger logically-supported argument?
2. Rate decisiveness: "Classicals win this exchange—[reason]" or "Keynesians edge it—[reason]" or "Tight exchange—both solid"
3. Be sharp, witty, fair. No fluff.

Keep it brief and decisive."""

    messages = [{"role": "user", "content": moderator_prompt}]
    try:
        result = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.3,
            max_tokens=150,
        )
        return result.choices[0].message.content.strip()
    except Exception as e:
        error_msg = str(e)
        if "rate_limit" in error_msg.lower() or "429" in error_msg:
            return "⏳ Moderator scoring unavailable (rate limit reached)."
        else:
            return "⚠️ Moderator scoring unavailable."


app_ui = ui.page_fluid(
    ui.head_content(
        ui.HTML(
            """
            <style>
            body {
                font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #f0f4ff 0%, #f6f2e8 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: #ffffff;
                border-radius: 12px;
                box-shadow: 0 10px 36px rgba(0, 0, 0, 0.08);
                padding: 28px;
            }
            .header {
                border-bottom: 3px solid #1b5e5a;
                padding-bottom: 16px;
                margin-bottom: 20px;
            }
            .header h1 {
                margin: 0 0 8px;
                color: #1e1c18;
            }
            .header p {
                margin: 0;
                color: #444;
            }
            .controls {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 16px;
                margin-bottom: 18px;
            }
            .controls label {
                font-weight: 600;
            }
            .controls textarea,
            .controls input,
            .controls select {
                width: 100%;
                padding: 10px 12px;
                border: 1px solid #c8c1b5;
                border-radius: 8px;
                font-size: 0.98rem;
            }
            .controls .full {
                grid-column: 1 / -1;
            }
            .actions {
                display: flex;
                gap: 12px;
                margin-bottom: 20px;
            }
            .actions button {
                padding: 10px 16px;
                border: none;
                border-radius: 999px;
                font-weight: 700;
                cursor: pointer;
            }
            .primary {
                background: linear-gradient(135deg, #1b5e5a, #2f7a6f);
                color: #ffffff;
            }
            .secondary {
                background: #e85d3f;
                color: #ffffff;
                transition: all 0.2s ease;
            }
            .secondary:hover {
                background: #d64c2e;
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(232, 93, 63, 0.3);
            }
            .status {
                padding: 10px 12px;
                background: #eef3ef;
                border-left: 4px solid #c28a2a;
                border-radius: 6px;
                margin-bottom: 18px;
            }
            .status.producing-voice {
                background: linear-gradient(135deg, #fff9e6 0%, #f0e6ff 100%);
                border-left: 4px solid #6b4ea0;
                animation: pulse-glow 1.5s ease-in-out infinite;
            }
            @keyframes pulse-glow {
                0%, 100% {
                    opacity: 1;
                    box-shadow: 0 0 10px rgba(107, 78, 160, 0.3);
                }
                50% {
                    opacity: 0.85;
                    box-shadow: 0 0 20px rgba(107, 78, 160, 0.6);
                }
            }
            .debate-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 16px;
            }
            .panel {
                border: 1px solid #e0d6c6;
                border-radius: 10px;
                padding: 14px;
                background: #faf8f4;
            }
            .panel h3 {
                margin-top: 0;
            }
            .turn {
                margin-bottom: 14px;
                padding-bottom: 12px;
                border-bottom: 1px dashed #d9cdbb;
            }
            .turn:last-child {
                border-bottom: none;
            }
            .turn .question {
                font-weight: 600;
                color: #2d2a25;
            }
            .turn .answer {
                margin-top: 6px;
                color: #333;
                white-space: pre-line;
            }
            @media (max-width: 900px) {
                .controls {
                    grid-template-columns: 1fr;
                }
                .debate-grid {
                    grid-template-columns: 1fr;
                }
            }
            </style>
            """
        )
    ),
    ui.div(
        ui.div(
            ui.h1("AI Persona Debate"),
            ui.p("Two teams respond to the same prompt: Classicals vs Keynesians."),
            class_="header",
        ),
        ui.div(
            ui.div(
                ui.tags.label("Debate topic"),
                ui.input_text("topic", "", placeholder="e.g., Money neutrality and the liquidity trap"),
                class_="full",
            ),
            ui.div(
                ui.tags.label("Round"),
                ui.input_select(
                    "round",
                    "",
                    {
                        "Round 1 - Neutrality": "Round 1 - Neutrality",
                        "Round 2 - Liquidity Preference": "Round 2 - Liquidity Preference",
                        "Round 3 - Policy at Low Rates": "Round 3 - Policy at Low Rates",
                    },
                ),
            ),
            ui.div(
                ui.tags.label("Student question"),
                ui.input_text_area(
                    "question",
                    "",
                    placeholder="Ask a focused question for both teams...",
                    height="110px",
                ),
                class_="full",
            ),
            class_="controls",
        ),
        ui.div(
            ui.input_action_button("debate", "Run Debate", class_="primary"),
            ui.input_action_button("audio_action", "Generate Audio", class_="primary"),
            ui.input_action_button("clear", "Clear", class_="secondary"),
            class_="actions",
        ),
        ui.output_ui("status"),
        ui.output_ui("audio_autoplay"),
        ui.div(
            ui.h3("📜 Debate Transcript", style="margin-top: 20px; color: #1e1c18;"),
            ui.output_ui("debate_transcript"),
            class_="panel",
            style="margin-top: 20px;",
        ),
        class_="container",
    ),
)


classical_history = reactive.Value([])
keynes_history = reactive.Value([])
status_message = reactive.Value("Ready.")


def render_history(history):
    if not history:
        return ui.p("No responses yet.", style="color: #999;")

    items = []
    for i, turn in enumerate(history, 1):
        # Show only the first 300 chars of the prompt (context) and full response
        prompt_preview = turn['user'][:150] + "..." if len(turn['user']) > 150 else turn['user']
        
        items.append(
            ui.div(
                ui.div(
                    ui.span(f"Turn {i}", style="font-weight: bold; color: #1b5e5a;"),
                    ui.p(prompt_preview, style="font-size: 0.85rem; color: #666; margin: 4px 0 8px;"),
                    ui.p(turn["assistant"], style="line-height: 1.6;"),
                    style="padding: 12px; background: #f9f9f9; border-left: 4px solid #1b5e5a;"
                ),
                class_="turn",
                style="margin-bottom: 12px;"
            )
        )
    return ui.div(*items)


def render_unified_debate(classical_history, keynes_history, moderator_scores, classical_audio_list, keynes_audio_list, moderator_audio_data):
    """Render a unified debate transcript showing both teams alternating, with moderator summary at end."""
    if not classical_history and not keynes_history:
        return ui.p("No debate yet. Submit a question to start.", style="color: #999;")
    
    items = []
    exchange = 1
    
    for i in range(max(len(classical_history), len(keynes_history))):
        # Show classical response
        if i < len(classical_history):
            classical_turn = classical_history[i]
            classical_audio = classical_audio_list[i] if i < len(classical_audio_list) else ""
            
            audio_html = (
                f"<audio controls preload='none' style='width: 100%; max-width: 420px; margin-top: 10px;'>"
                f"<source src='data:audio/mp3;base64,{classical_audio}' type='audio/mpeg'></audio>"
                if classical_audio else ""
            )
            
            items.append(
                ui.div(
                    ui.div(
                        ui.span(f"Exchange {exchange} — Classicals (Walras & Marshall)", 
                               style="font-weight: bold; color: #2c5aa0; font-size: 0.95rem;"),
                        ui.p(classical_turn["assistant"], style="margin-top: 8px; line-height: 1.6; color: #333;"),
                        ui.HTML(audio_html),
                        style="padding: 12px; background: #eef3ff; border-left: 4px solid #2c5aa0;"
                    ),
                    style="margin-bottom: 12px;"
                )
            )
        
        # Show keynesian response
        if i < len(keynes_history):
            keynes_turn = keynes_history[i]
            keynes_audio = keynes_audio_list[i] if i < len(keynes_audio_list) else ""
            
            audio_html = (
                f"<audio controls preload='none' style='width: 100%; max-width: 420px; margin-top: 10px;'>"
                f"<source src='data:audio/mp3;base64,{keynes_audio}' type='audio/mpeg'></audio>"
                if keynes_audio else ""
            )
            
            items.append(
                ui.div(
                    ui.div(
                        ui.span(f"Exchange {exchange} — Keynesians (Keynes & Hicks)", 
                               style="font-weight: bold; color: #a0572c; font-size: 0.95rem;"),
                        ui.p(keynes_turn["assistant"], style="margin-top: 8px; line-height: 1.6; color: #333;"),
                        ui.HTML(audio_html),
                        style="padding: 12px; background: #fff5e6; border-left: 4px solid #a0572c;"
                    ),
                    style="margin-bottom: 12px;"
                )
            )
            exchange += 1
    
    # Add moderator summary at the end
    if moderator_scores:
        moderator_audio_html = (
            f"<audio id='moderator-scorecard-audio' controls preload='none' "
            f"style='width: 100%; max-width: 520px; margin-top: 12px;'>"
            f"<source src='data:audio/mp3;base64,{moderator_audio_data}' type='audio/mpeg'></audio>"
            if moderator_audio_data else ""
        )
        
        items.append(
            ui.div(
                ui.HTML("<hr style='margin: 20px 0; border: none; border-top: 2px solid #d4af37;'>"),
                ui.div(
                    ui.span("🏆 Moderator's Final Scorecard", 
                           style="font-weight: bold; color: #8b6914; font-size: 1.1rem; display: block; margin-bottom: 12px;"),
                    ui.HTML("<br>".join(
                        f"<div style='margin-bottom: 10px;'><strong>Exchange {i+1}:</strong> {score}</div>" 
                        for i, score in enumerate(moderator_scores)
                    )),
                    ui.HTML(moderator_audio_html),
                    style="padding: 16px; background: #fffbf0; border-left: 4px solid #d4af37; border-radius: 6px;"
                ),
                style="margin-top: 20px;"
            )
        )
    
    return ui.div(*items)


classical_history = reactive.Value([])
keynes_history = reactive.Value([])
classical_audio = reactive.Value([])  # Store audio for classical responses
keynes_audio = reactive.Value([])  # Store audio for keynesian responses
moderator_audio = reactive.Value("")  # Store audio for moderator scorecard
moderator_scores = reactive.Value([])
status_message = reactive.Value("Ready.")
current_topic = reactive.Value("")
audio_state = reactive.Value("empty")  # empty | idle | processing | ready | error
audio_error = reactive.Value("")
audio_play_request = reactive.Value(0)


def server(input, output, session):
    audio_worker = {"done": False, "result": None, "error": ""}

    def _debate_exists():
        return bool(classical_history.get()) and bool(keynes_history.get())

    def _set_audio_button_label():
        state = audio_state.get()
        if state == "processing":
            label = "Processing Audio..."
        elif state == "ready":
            label = "Play Audio"
        elif state == "error":
            label = "Retry Audio"
        elif _debate_exists():
            label = "Generate Audio"
        else:
            label = "Generate Audio"
        ui.update_action_button("audio_action", label=label)

    def _generate_audio_background(c_hist, k_hist, scores):
        try:
            c_audio = []
            k_audio = []

            for turn in c_hist:
                c_audio.append(text_to_speech(turn["assistant"], CLASSICAL_VOICE, CLASSICAL_PITCH))
            for turn in k_hist:
                k_audio.append(text_to_speech(turn["assistant"], KEYNESIAN_VOICE, KEYNESIAN_PITCH))

            moderator_text = " ".join(scores) if scores else ""
            m_audio = text_to_speech(moderator_text, MODERATOR_VOICE, MODERATOR_PITCH) if moderator_text else ""

            audio_worker["result"] = {"classical": c_audio, "keynes": k_audio, "moderator": m_audio}
            audio_worker["error"] = ""
        except Exception as e:
            audio_worker["result"] = None
            audio_worker["error"] = str(e)
        finally:
            audio_worker["done"] = True

    @reactive.effect
    def _auto_clear_on_topic_change():
        """Clear debate history when topic changes"""
        new_topic = input.topic().strip()
        
        # If topic is empty, don't auto-clear yet
        if not new_topic:
            return
        
        # If topic changed from previous, auto-clear the history
        if current_topic.get() != new_topic and classical_history.get():
            classical_history.set([])
            keynes_history.set([])
            classical_audio.set([])
            keynes_audio.set([])
            moderator_audio.set("")
            moderator_scores.set([])
            audio_state.set("empty")
            audio_error.set("")
            status_message.set(f'✨ New topic: "{new_topic}" — Ready to debate!')
            current_topic.set(new_topic)
            _set_audio_button_label()

    @reactive.effect
    @reactive.event(input.clear)
    def _clear_all():
        classical_history.set([])
        keynes_history.set([])
        classical_audio.set([])
        keynes_audio.set([])
        moderator_audio.set("")
        moderator_scores.set([])
        audio_state.set("empty")
        audio_error.set("")
        current_topic.set("")
        _set_audio_button_label()
        status_message.set("🗑️ Cleared. Enter a topic and question to start fresh.")

    @reactive.effect
    @reactive.event(input.debate)
    def _run_debate():
        topic = input.topic().strip()
        question = input.question().strip()
        round_label = input.round()

        if not topic or not question:
            status_message.set("❌ Please enter a topic and a question.")
            return

        classical_audio.set([])
        keynes_audio.set([])
        moderator_audio.set("")
        audio_state.set("empty")
        audio_error.set("")
        _set_audio_button_label()

        # Track the current topic
        current_topic.set(topic)
        status_message.set(f"🎙️ Starting debate on '{topic}'...")

        # EXCHANGE 1: Classicals open, then Keynesians respond to them
        classical_msgs = build_messages(
            SYSTEM_CLASSICAL,
            topic,
            round_label,
            classical_history.get(),
            question,
        )
        classical_reply = get_ai_response(classical_msgs)
        
        # Check for API errors
        if classical_reply.startswith(("⏳", "🔑", "⚠️")):
            status_message.set(f"❌ {classical_reply}")
            return

        # Keynesians respond to the Classical argument
        keynes_opening = f"The Classicals just argued: \"{classical_reply}\"\n\nNow, respond to the student question AND address their Classical argument."
        keynes_msgs = build_messages(
            SYSTEM_KEYNESIAN,
            topic,
            round_label,
            keynes_history.get(),
            keynes_opening,
        )
        keynes_reply = get_ai_response(keynes_msgs)
        
        # Check for API errors
        if keynes_reply.startswith(("⏳", "🔑", "⚠️")):
            # Show partial debate with error message
            classical_history.set(
                classical_history.get() + [{"user": question, "assistant": classical_reply}]
            )
            status_message.set(f"❌ {keynes_reply} (Partial debate shown)")
            return
        
        # ✨ SHOW EXCHANGE 1 IMMEDIATELY (no audio yet)
        classical_history.set(
            classical_history.get() + [{"user": question, "assistant": classical_reply}]
        )
        keynes_history.set(
            keynes_history.get() + [{"user": keynes_opening, "assistant": keynes_reply}]
        )
        status_message.set("✅ Exchange 1 ready! Continuing debate...")

        # EXCHANGE 2: Classicals counter-argue
        classical_counter = f"The Keynesians just countered: \"{keynes_reply}\"\n\nProvide a counter-argument to their position."
        classical_msgs_2 = build_messages(
            SYSTEM_CLASSICAL,
            topic,
            round_label,
            classical_history.get(),
            classical_counter,
        )
        classical_counter_reply = get_ai_response(classical_msgs_2)
        
        # Check for API errors
        if classical_counter_reply.startswith(("⏳", "🔑", "⚠️")):
            status_message.set(f"❌ {classical_counter_reply} (Exchange 1 shown, debate incomplete)")
            return

        # EXCHANGE 2: Keynesians rebut
        keynes_rebuttal = f"The Classicals just countered with: \"{classical_counter_reply}\"\n\nProvide your final rebuttal."
        keynes_msgs_2 = build_messages(
            SYSTEM_KEYNESIAN,
            topic,
            round_label,
            keynes_history.get(),
            keynes_rebuttal,
        )
        keynes_rebuttal_reply = get_ai_response(keynes_msgs_2)
        
        # Check for API errors
        if keynes_rebuttal_reply.startswith(("⏳", "🔑", "⚠️")):
            status_message.set(f"❌ {keynes_rebuttal_reply} (Exchanges 1-2 shown, debate incomplete)")
            return
        
        # ✨ SHOW EXCHANGE 2 IMMEDIATELY (no audio yet)
        classical_history.set(
            classical_history.get() + [{"user": classical_counter, "assistant": classical_counter_reply}]
        )
        keynes_history.set(
            keynes_history.get() + [{"user": keynes_rebuttal, "assistant": keynes_rebuttal_reply}]
        )
        status_message.set("✅ Exchange 2 ready! Final exchange...")

        # EXCHANGE 3: Classicals final response
        classical_final = f"The Keynesians just argued: \"{keynes_rebuttal_reply}\"\n\nDeliver your final response to their argument."
        classical_msgs_3 = build_messages(
            SYSTEM_CLASSICAL,
            topic,
            round_label,
            classical_history.get(),
            classical_final,
        )
        classical_final_reply = get_ai_response(classical_msgs_3)
        
        # Check for API errors
        if classical_final_reply.startswith(("⏳", "🔑", "⚠️")):
            status_message.set(f"❌ {classical_final_reply} (Exchanges 1-2 shown, debate incomplete)")
            return

        # EXCHANGE 3: Keynesians final word
        keynes_final = f"The Classicals just concluded: \"{classical_final_reply}\"\n\nDeliver your final word on this debate."
        keynes_msgs_3 = build_messages(
            SYSTEM_KEYNESIAN,
            topic,
            round_label,
            keynes_history.get(),
            keynes_final,
        )
        keynes_final_reply = get_ai_response(keynes_msgs_3)
        
        # Check for API errors
        if keynes_final_reply.startswith(("⏳", "🔑", "⚠️")):
            # Show exchanges 1-3 (Classical final included)
            classical_history.set(
                classical_history.get() + [{"user": keynes_final, "assistant": classical_final_reply}]
            )
            status_message.set(f"❌ {keynes_final_reply} (Exchanges 1-3 shown, debate incomplete)")
            return
        
        # ✨ SHOW EXCHANGE 3 IMMEDIATELY (no audio yet)
        classical_history.set(
            classical_history.get() + [{"user": keynes_final, "assistant": classical_final_reply}]
        )
        keynes_history.set(
            keynes_history.get() + [{"user": keynes_final, "assistant": keynes_final_reply}]
        )

        # Get moderator analysis for all exchanges
        status_message.set("📋 Moderator is scoring all exchanges...")
        moderator_comment_1 = get_moderator_analysis(topic, round_label, classical_reply, keynes_reply)
        moderator_comment_2 = get_moderator_analysis(topic, round_label, classical_counter_reply, keynes_rebuttal_reply)
        moderator_comment_3 = get_moderator_analysis(topic, round_label, classical_final_reply, keynes_final_reply)
        
        moderator_scores.set([moderator_comment_1, moderator_comment_2, moderator_comment_3])
        
        # Clear any old audio data
        classical_audio.set([])
        keynes_audio.set([])
        moderator_audio.set("")
        audio_state.set("idle")
        audio_error.set("")
        _set_audio_button_label()
        
        status_message.set(f"✅ Debate complete! Scroll down to read the full exchange. Ready for next question on '{topic}'.")

    @reactive.effect
    @reactive.event(input.audio_action)
    def _audio_action():
        if not _debate_exists():
            status_message.set("Error: Run a debate first, then generate audio.")
            return
        if audio_state.get() == "processing":
            return
        if audio_state.get() == "ready":
            audio_play_request.set(audio_play_request.get() + 1)
            return

        classical_audio.set([])
        keynes_audio.set([])
        moderator_audio.set("")
        audio_worker["done"] = False
        audio_worker["result"] = None
        audio_worker["error"] = ""
        audio_state.set("processing")
        audio_error.set("")
        _set_audio_button_label()
        c_hist = list(classical_history.get())
        k_hist = list(keynes_history.get())
        scores = list(moderator_scores.get())
        status_message.set("Generating audio in the background... you can keep reading the transcript.")
        threading.Thread(target=_generate_audio_background, args=(c_hist, k_hist, scores), daemon=True).start()

    @reactive.effect
    def _poll_audio_worker():
        reactive.invalidate_later(0.5)
        if audio_state.get() != "processing":
            return
        if not audio_worker["done"]:
            return

        audio_worker["done"] = False
        if audio_worker["error"]:
            audio_state.set("error")
            audio_error.set(audio_worker["error"])
            status_message.set("Audio generation failed. Click Retry Audio.")
            _set_audio_button_label()
            return

        result = audio_worker["result"] or {}
        classical_audio.set(result.get("classical", []))
        keynes_audio.set(result.get("keynes", []))
        moderator_audio.set(result.get("moderator", ""))
        audio_state.set("ready")
        audio_error.set("")
        _set_audio_button_label()
        status_message.set("Audio is ready. Click Play Audio or use the inline players.")

    @reactive.effect
    def _sync_audio_button():
        audio_state.get()
        classical_history.get()
        keynes_history.get()
        _set_audio_button_label()

    @output
    @render.ui
    def status():
        msg = status_message.get()
        # Add special class for voice production messages
        if "🎤" in msg or "Producing" in msg or "audio" in msg.lower():
            return ui.div(msg, class_="status producing-voice")
        return ui.div(msg, class_="status")

    @output
    @render.ui
    def audio_autoplay():
        _ = audio_play_request.get()
        if audio_state.get() != "ready":
            return ui.HTML("")
        return ui.HTML(
            """
            <script>
            setTimeout(function() {
              const el = document.getElementById('moderator-scorecard-audio') || document.querySelector('audio');
              if (el) { el.play().catch(() => {}); }
            }, 30);
            </script>
            """
        )

    @output
    @render.ui
    def debate_transcript():
        return render_unified_debate(
            classical_history.get(), 
            keynes_history.get(), 
            moderator_scores.get(), 
            classical_audio.get(), 
            keynes_audio.get(),
            moderator_audio.get()
        )


app = App(app_ui, server)
