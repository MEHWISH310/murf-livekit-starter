import logging
import asyncio
import sys
import json
from pathlib import Path

# Make backend/src importable (prompt.py, db.py, weather_tool.py, scheme_tool.py live there)
SRC_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SRC_DIR))

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    tokenize,
    room_io,
    function_tool,
    RunContext,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from prompt import SYSTEM_PROMPT
from db import get_user, normalize_user_id, start_call, finish_call
from weather_tool import get_district_forecast, WeatherLookupError
from scheme_tool import find_schemes, list_all_schemes

logger = logging.getLogger("outbound-agent")

load_dotenv(SRC_DIR.parent / ".env.local")

AGENT_NAME = "kisan-sahay-outbound"

OUTBOUND_CALL_RULES = """

OUTBOUND CALL RULES:
- This call was placed by Kisan Sahay. The farmer did not request it and does not know who is calling yet.
- Your very first turn must be spoken text only — do not call any tool or function on this first turn, even if you plan to use one soon after.
- In that first turn, in no more than two short sentences, say clearly: who is calling (Kisan Sahay, the farming voice assistant), why you are calling (a weather warning relevant to their crop), and how to stop future calls (they can say "don't call me again" or "mujhe dobara call mat karo" at any point).
- Only after that opening has been spoken, and only on a later turn, may you call a tool such as the weather lookup.
- If the farmer asks to not be called again, or sounds annoyed, acknowledge it, apologize briefly, and end the call politely without pushing further.
- Keep the call short — this is an alert, not a long conversation, unless the farmer asks follow-up questions.
"""


class OutboundAssistant(Agent):
    def __init__(self, farmer_name: str, district: str, call_id: int) -> None:
        context_note = "\n\nCALL CONTEXT:"
        if farmer_name:
            context_note += f"\n- The farmer's name is {farmer_name}."
        else:
            context_note += "\n- You do not know the farmer's name yet. Ask for it naturally after your opening."
        if district:
            context_note += (
                f"\n- Once your opening line has been spoken, check the weather for {district} "
                "using your weather tool, on a separate turn, and then tell the farmer about it."
            )
        else:
            context_note += "\n- You do not have a district yet. Ask for it after your opening, then check the weather."

        super().__init__(instructions=SYSTEM_PROMPT + OUTBOUND_CALL_RULES + context_note)
        self._farmer_name = farmer_name
        self._district = district
        self._call_id = call_id
        self._outcome: str | None = None
        self._reason: str = ""

    @function_tool
    async def lookup_caller(self, context: RunContext, name: str):
        """Look up whether this farmer has talked to Kisan Sahay before, using their name.

        Args:
            name: The farmer's name.
        """
        user_id = normalize_user_id(name)
        user = get_user(user_id)
        if user is None:
            return f"No previous record found for {name}."
        facts = dict(user["facts"] or {})
        facts_summary = ", ".join(f"{k}: {v}" for k, v in facts.items()) if facts else "no farm details saved"
        return f"Found returning farmer {user['name']}. Known details — {facts_summary}."

    @function_tool
    async def get_weather_forecast(self, context: RunContext, district: str):
        """Look up today's weather forecast for a district in India, using a live weather service.

        Args:
            district: The district or area name to check the forecast for.
        """
        try:
            forecast = await get_district_forecast(district)
            logger.info(f"get_weather_forecast: success for '{district}': {forecast}")
            self._outcome = "success"
            self._reason = "weather_delivered"
            return (
                f"Forecast for {forecast['location']}, dated {forecast['date']}: "
                f"high of {forecast['temp_max']}°C, low of {forecast['temp_min']}°C, "
                f"expected rainfall {forecast['precipitation_mm']}mm."
            )
        except WeatherLookupError as e:
            logger.warning(f"get_weather_forecast: failed for '{district}': {e}")
            return "The weather lookup failed right now. Say so honestly, do not invent a forecast."

    @function_tool
    async def get_government_scheme_info(self, context: RunContext, scheme_query: str):
        """Look up information about Indian government schemes for farmers, from a local reference dataset.

        Args:
            scheme_query: A scheme name or topic like "insurance" or "loan".
        """
        matches = find_schemes(scheme_query)
        if not matches:
            all_names = ", ".join(s["name"] for s in list_all_schemes())
            return f"No scheme matched. Known schemes: {all_names}."
        s = matches[0]
        self._outcome = "success"
        self._reason = "scheme_info_delivered"
        return f"{s['name']} ({s['full_name']}): {s['description']} Eligibility — {s['eligibility']}"


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name=AGENT_NAME)
async def outbound_agent(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    metadata = {}
    if ctx.job.metadata:
        try:
            metadata = json.loads(ctx.job.metadata)
        except json.JSONDecodeError:
            logger.warning("Could not parse job metadata as JSON")

    farmer_name = metadata.get("farmer_name", "")
    district = metadata.get("district", "")

    call_id = start_call(channel="sip", farmer_name=farmer_name)

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(model="gemini-3.5-flash-lite"),
        tts=murf.TTS(
            voice="Anisha",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    assistant = OutboundAssistant(farmer_name=farmer_name, district=district, call_id=call_id)

    async def on_shutdown():
        outcome = assistant._outcome or "failure"
        reason = assistant._reason or "no_clear_outcome"
        finish_call(call_id, outcome=outcome, reason=reason)
        logger.info(f"outbound call #{call_id} finished: outcome={outcome}, reason={reason}")

    ctx.add_shutdown_callback(on_shutdown)

    await session.start(
        agent=assistant,
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: noise_cancellation.BVCTelephony(),
            ),
        ),
    )

    await ctx.connect()

    # Give the call a moment to fully settle (ringing → answered → audio path
    # established) before the agent starts speaking, so the opening line
    # isn't cut off or spoken into dead air on the farmer's end.
    await asyncio.sleep(8)

    # Simple trigger only — all context (name, district, opening rules) already
    # lives in the agent's instructions, so this stays a plain instruction
    # with no dynamic per-call content, avoiding Gemini's turn-ordering error.
    await session.generate_reply(
        instructions="Begin the call now, following your OUTBOUND CALL RULES exactly for your opening line."
    )


if __name__ == "__main__":
    cli.run_app(server)