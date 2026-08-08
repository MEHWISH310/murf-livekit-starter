import logging

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
    inference,
    tokenize,
    room_io,
    UserInputTranscribedEvent,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from prompt import SYSTEM_PROMPT
from db import init_db, get_user, save_user, delete_user, normalize_user_id

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Make sure the users table exists before any session tries to use it
init_db()


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        self._current_user_id: str | None = None

    @function_tool
    async def lookup_caller(self, context: RunContext, name: str):
        """Look up whether this farmer has talked to Kisan Sahay before, using their name.

        Call this as soon as the farmer tells you their name, before you rely on that name for anything else. If the farmer already gave their name earlier in this same call, do not call this again.

        Args:
            name: The farmer's name exactly as they said it.
        """
        user_id = normalize_user_id(name)
        self._current_user_id = user_id
        user = get_user(user_id)

        if user is None:
            logger.info(f"lookup_caller: no existing record for '{name}' — new caller")
            return f"No previous record found for {name}. Treat them as a new farmer."

        facts = user["facts"] or {}
        facts_summary = ", ".join(f"{k}: {v}" for k, v in facts.items()) if facts else "no farm details saved yet"
        logger.info(f"lookup_caller: found existing record for '{name}': {facts}")
        return (
            f"Found a returning farmer named {user['name']}. "
            f"Known details — {facts_summary}. "
            "Greet them warmly by name and naturally refer to what you already know, "
            "don't ask them to repeat it."
        )

    @function_tool
    async def save_caller_info(
        self,
        context: RunContext,
        name: str,
        consent: bool,
        language_preference: str | None = None,
        crops: str | None = None,
        land_size: str | None = None,
        district: str | None = None,
        irrigation_type: str | None = None,
    ):
        """Save or update what you know about this farmer, if they have agreed to be remembered.

        Always call this after asking the farmer whether it's okay to remember them. Set consent to true only if they clearly agreed, or false if they declined or you have not asked yet. Pass an honest consent value every time — this function itself decides whether anything actually gets written to storage based on that flag, so do not decide on your own whether to call it.

        Args:
            name: The farmer's name exactly as they said it.
            consent: True only if the farmer has clearly agreed to be remembered, false otherwise.
            language_preference: The language or style they're speaking in, e.g. "Hindi", "Hinglish", "English".
            crops: Crops the farmer grows, as a short comma-separated list.
            land_size: Approximate land size the farmer mentioned, in their own words.
            district: District or area the farmer mentioned.
            irrigation_type: Irrigation method the farmer mentioned, e.g. "borewell", "canal", "rain-fed".
        """
        if not consent:
            logger.info(f"save_caller_info: consent is false for '{name}' — not writing to storage")
            return "Not saved. The farmer has not agreed to be remembered, so nothing was written to storage."

        user_id = normalize_user_id(name)
        self._current_user_id = user_id

        facts = {}
        if crops:
            facts["crops"] = crops
        if land_size:
            facts["land_size"] = land_size
        if district:
            facts["district"] = district
        if irrigation_type:
            facts["irrigation_type"] = irrigation_type

        save_user(user_id, name, language_preference, facts)
        logger.info(f"save_caller_info: saved for '{name}': {facts}")
        return "Saved."

    @function_tool
    async def forget_me(self, context: RunContext, name: str):
        """Delete everything Kisan Sahay remembers about this farmer.

        Only call this if the farmer explicitly asks to be forgotten, asks you to delete their data, or asks you to stop remembering them — never call it on your own. Always confirm with the farmer once first (ask if they're sure, since this can't be undone), and only call this tool after they confirm.

        Args:
            name: The farmer's name exactly as they said it (the name they gave earlier in this call).
        """
        user_id = normalize_user_id(name)
        delete_user(user_id)
        logger.info(f"forget_me: deleted record for '{name}'")
        return f"All saved information about {name} has been deleted. Treat them as a brand new farmer from now on."

    # To add tools, use the @function_tool decorator.
    # Here's an example that adds a simple weather tool.
    # You also have to add `from livekit.agents import function_tool, RunContext` to the top of this file
    # @function_tool
    # async def lookup_weather(self, context: RunContext, location: str):
    #     """Use this tool to look up current weather information in the given location.
    #
    #     If the location is not supported by the weather service, the tool will indicate this. You must tell the user the location's weather is unavailable.
    #
    #     Args:
    #         location: The location to look up weather information for (e.g. city name)
    #     """
    #
    #     logger.info(f"Looking up weather for {location}")
    #
    #     return "sunny with a temperature of 70 degrees."


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-3", language="multi"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
                model="gemini-3.5-flash-lite",
            ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
                voice="Anisha",
                style="Conversation",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True
            ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # Log detected language register for each user turn (Hindi / Hinglish / English)
    @session.on("user_input_transcribed")
    def on_user_input_transcribed(ev: UserInputTranscribedEvent):
        transcript = ev.transcript.strip().lower()
        if not transcript:
            return

        # Check for Devanagari script characters (native Hindi)
        has_devanagari = any(0x0900 <= ord(c) <= 0x097F for c in transcript)

        # Check for common Hinglish / romanized Hindi keywords (farming-focused)
        hindi_keywords = {
            "kya", "hai", "aur", "main", "nahin", "aap", "namaste", "shukriya",
            "mein", "ke", "ki", "se", "ko", "ka", "jo", "toh", "bhi", "ho",
            "kar", "raha", "rahi", "rha", "mujhe", "mera", "meri", "hum",
            "tum", "apna", "apni", "karke", "karo", "karna", "tha", "thi",
            "the", "ab", "kab", "sab", "khet", "fasal", "beej", "kheti",
            "kisan", "mandi", "barish", "bhaav", "paani",
        }
        has_hindi_keywords = any(word in transcript.split() for word in hindi_keywords)

        if has_devanagari:
            logger.info(f"Detected language register: Hindi (Devanagari) — '{transcript}'")
        elif has_hindi_keywords:
            logger.info(f"Detected language register: Hinglish (romanized) — '{transcript}'")
        else:
            logger.info(f"Detected language register: English — '{transcript}'")

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()

    await session.generate_reply(
        instructions="Greet the farmer warmly, introduce yourself as Kisan Sahay, ask their name, and ask how you can help them today."
    )


if __name__ == "__main__":
    cli.run_app(server)