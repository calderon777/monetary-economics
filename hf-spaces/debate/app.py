from shiny import App, ui, render, reactive
from groq import Groq
import os
import edge_tts
import asyncio
import base64
from io import BytesIO

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

# Voice settings for each team - older, more distinguished voices
CLASSICAL_VOICE = "en-GB-AlfieNeural"  # Older British male for Walras/Marshall
KEYNESIAN_VOICE = "en-US-GuyNeural"  # Distinguished older American male for Keynes/Hicks

# Speech parameters for debate-like delivery
SPEECH_RATE = "+5%"  # Slightly faster for debate energy
CLASSICAL_PITCH = "-10Hz"  # Lower pitch for gravitas
KEYNESIAN_PITCH = "+0Hz"  # Natural pitch


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
    result = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.4,
        max_tokens=400,
    )
    return result.choices[0].message.content.strip()


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
    result = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.3,
        max_tokens=150,
    )
    return result.choices[0].message.content.strip()


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
            ui.input_action_button("clear", "Clear", class_="secondary"),
            class_="actions",
        ),
        ui.output_ui("status"),
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


def render_unified_debate(classical_history, keynes_history, moderator_scores, classical_audio_list, keynes_audio_list):
    """Render a unified debate transcript showing both teams alternating, with moderator summary at end."""
    if not classical_history and not keynes_history:
        return ui.p("No debate yet. Submit a question to start.", style="color: #999;")
    
    items = []
    exchange = 1
    audio_id = 0  # Track audio elements for sequential playback
    
    # Add JavaScript for sequential audio playback
    autoplay_script = """
    <script>
    function setupDebateAudioChain() {
        const audioElements = document.querySelectorAll('audio[data-debate-audio]');
        
        audioElements.forEach((audio, index) => {
            // When this audio ends, play the next one after a brief pause
            audio.addEventListener('ended', () => {
                if (index < audioElements.length - 1) {
                    setTimeout(() => {
                        audioElements[index + 1].play().catch(e => console.log('Autoplay prevented:', e));
                    }, 800);  // 800ms pause between speakers (debate-like)
                }
            });
        });
        
        // Auto-play the first audio with a slight delay
        if (audioElements.length > 0) {
            setTimeout(() => {
                audioElements[0].play().catch(e => {
                    console.log('Initial autoplay prevented - user interaction required:', e);
                });
            }, 500);
        }
    }
    
    // Run when page loads
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupDebateAudioChain);
    } else {
        setupDebateAudioChain();
    }
    // Also run immediately for dynamic updates
    setTimeout(setupDebateAudioChain, 100);
    </script>
    """
    
    items.append(ui.HTML(autoplay_script))
    
    for i in range(max(len(classical_history), len(keynes_history))):
        # Show classical response
        if i < len(classical_history):
            classical_turn = classical_history[i]
            classical_audio = classical_audio_list[i] if i < len(classical_audio_list) else ""
            
            audio_html = ""
            if classical_audio:
                audio_html = f"""
                <div style="margin-top: 12px; padding: 8px; background: rgba(44, 90, 160, 0.05); border-radius: 6px;">
                    <div style="font-size: 0.85rem; color: #2c5aa0; margin-bottom: 4px;">🎙️ Listen to Classicals</div>
                    <audio id="debate-audio-{audio_id}" data-debate-audio controls style="width: 100%; height: 32px;">
                        <source src="data:audio/mp3;base64,{classical_audio}" type="audio/mp3">
                        Your browser does not support audio playback.
                    </audio>
                </div>
                """
                audio_id += 1
            
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
            
            audio_html = ""
            if keynes_audio:
                audio_html = f"""
                <div style="margin-top: 12px; padding: 8px; background: rgba(160, 87, 44, 0.05); border-radius: 6px;">
                    <div style="font-size: 0.85rem; color: #a0572c; margin-bottom: 4px;">🎙️ Listen to Keynesians</div>
                    <audio id="debate-audio-{audio_id}" data-debate-audio controls style="width: 100%; height: 32px;">
                        <source src="data:audio/mp3;base64,{keynes_audio}" type="audio/mp3">
                        Your browser does not support audio playback.
                    </audio>
                </div>
                """
                audio_id += 1
            
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
moderator_scores = reactive.Value([])
status_message = reactive.Value("Ready.")
current_topic = reactive.Value("")


def server(input, output, session):
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
            status_message.set(f'✨ New topic: "{new_topic}" — Ready to debate!')
            current_topic.set(new_topic)

    @reactive.effect
    @reactive.event(input.clear)
    def _clear_all():
        classical_history.set([])
        keynes_history.set([])
        classical_audio.set([])
        keynes_audio.set([])
        moderator_scores.set([])
        current_topic.set("")
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

        # Track the current topic
        current_topic.set(topic)
        status_message.set(f"🎙️ Starting debate on '{topic}'... Classicals preparing opening statement...")

        # Lists to store audio for this debate session
        classical_audio_batch = []
        keynes_audio_batch = []

        # EXCHANGE 1: Classicals open, then Keynesians respond to them
        classical_msgs = build_messages(
            SYSTEM_CLASSICAL,
            topic,
            round_label,
            classical_history.get(),
            question,
        )
        classical_reply = get_ai_response(classical_msgs)
        status_message.set("🎤 Generating Classicals' audio & preparing Keynesian response...")
        classical_audio_1 = text_to_speech(classical_reply, CLASSICAL_VOICE, CLASSICAL_PITCH)
        classical_audio_batch.append(classical_audio_1)

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
        status_message.set("🎤 Generating Keynesians' audio & preparing Classicals' counter...")
        keynes_audio_1 = text_to_speech(keynes_reply, KEYNESIAN_VOICE, KEYNESIAN_PITCH)
        keynes_audio_batch.append(keynes_audio_1)

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
        status_message.set("🎤 Generating Classicals' counter-argument audio...")
        classical_audio_2 = text_to_speech(classical_counter_reply, CLASSICAL_VOICE, CLASSICAL_PITCH)
        classical_audio_batch.append(classical_audio_2)

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
        status_message.set("🎤 Generating Keynesians' rebuttal audio...")
        keynes_audio_2 = text_to_speech(keynes_rebuttal_reply, KEYNESIAN_VOICE, KEYNESIAN_PITCH)
        keynes_audio_batch.append(keynes_audio_2)

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
        status_message.set("🎤 Generating Classicals' final response audio...")
        classical_audio_3 = text_to_speech(classical_final_reply, CLASSICAL_VOICE, CLASSICAL_PITCH)
        classical_audio_batch.append(classical_audio_3)

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
        status_message.set("🎤 Generating Keynesians' final word audio...")
        keynes_audio_3 = text_to_speech(keynes_final_reply, KEYNESIAN_VOICE, KEYNESIAN_PITCH)
        keynes_audio_batch.append(keynes_audio_3)

        # Store all exchanges in history
        classical_history.set(
            classical_history.get() + [
                {"user": question, "assistant": classical_reply},
                {"user": keynes_rebuttal, "assistant": classical_counter_reply},
                {"user": keynes_final, "assistant": classical_final_reply}
            ]
        )
        keynes_history.set(
            keynes_history.get() + [
                {"user": keynes_opening, "assistant": keynes_reply},
                {"user": keynes_rebuttal, "assistant": keynes_rebuttal_reply},
                {"user": classical_final, "assistant": keynes_final_reply}
            ]
        )
        
        # Store audio for all exchanges
        classical_audio.set(classical_audio.get() + classical_audio_batch)
        keynes_audio.set(keynes_audio.get() + keynes_audio_batch)

        # Get moderator analysis for all exchanges at the end
        status_message.set("📋 Moderator is scoring all exchanges...")
        moderator_comment_1 = get_moderator_analysis(topic, round_label, classical_reply, keynes_reply)
        moderator_comment_2 = get_moderator_analysis(topic, round_label, classical_counter_reply, keynes_rebuttal_reply)
        moderator_comment_3 = get_moderator_analysis(topic, round_label, classical_final_reply, keynes_final_reply)
        
        moderator_scores.set([moderator_comment_1, moderator_comment_2, moderator_comment_3])

        status_message.set(f"✅ Debate complete! 3 exchanges scored. Ready for your next question on '{topic}' — or change the topic and Clear to start fresh.")

    @output
    @render.ui
    def status():
        return ui.div(status_message.get(), class_="status")

    @output
    @render.ui
    def debate_transcript():
        return render_unified_debate(
            classical_history.get(), 
            keynes_history.get(), 
            moderator_scores.get(), 
            classical_audio.get(), 
            keynes_audio.get()
        )


app = App(app_ui, server)
