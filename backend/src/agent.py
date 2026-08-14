import logging

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
    tokenize,
    room_io,
    UserInputTranscribedEvent,
    function_tool,
    RunContext,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from prompt import SYSTEM_PROMPT
from db import (
    init_db,
    get_user,
    save_user,
    delete_user,
    normalize_user_id,
    create_escalation as db_create_escalation,
    start_call,
    finish_call,
)
from weather_tool import get_district_forecast, WeatherLookupError
from scheme_tool import find_schemes, list_all_schemes
from crop_specialist import CropSpecialistAgent

logger = logging.getLogger("agent")

load_dotenv(".env.local")

init_db()


class Assistant(Agent):
    def __init__(self, call_id: int) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        self._current_user_id: str | None = None
        self._call_id = call_id
        self._outcome: str | None = None
        self._reason: str = ""
        self._farmer_name: str = ""

    @function_tool
    async def lookup_caller(self, context: RunContext, name: str):
        """Look up whether this farmer has talked to Kisan Sahay before, using their name.

        Call this as soon as the farmer tells you their name, before you rely on that name for anything else. If the farmer already gave their name earlier in this same call, do not call this again.

        Args:
            name: The farmer's name exactly as they said it.
        """
        user_id = normalize_user_id(name)
        self._current_user_id = user_id
        self._farmer_name = name
        user = get_user(user_id)

        if user is None:
            logger.info(f"lookup_caller: no existing record for '{name}' — new caller")
            return f"No previous record found for {name}. Treat them as a new farmer."

        facts = dict(user["facts"] or {})
        last_topic = facts.pop("last_topic", None)
        facts_summary = ", ".join(f"{k}: {v}" for k, v in facts.items()) if facts else "no farm details saved yet"
        logger.info(f"lookup_caller: found existing record for '{name}': {user['facts']}")
        topic_line = f" Last time you helped them with: {last_topic}." if last_topic else ""
        return (
            f"Found a returning farmer named {user['name']}. "
            f"Known details — {facts_summary}.{topic_line} "
            "Greet them warmly by name, naturally refer to what you already know, "
            "and if there's a last topic, mention it too — don't ask them to repeat any of it."
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
        last_topic: str | None = None,
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
            last_topic: A short summary (under 10 words) of the main thing you helped with in this call, e.g. "wheat sowing timing" or "pest spots on cotton leaves". Overwrites whatever was saved as the last topic before.
        """
        if not consent:
            logger.info(f"save_caller_info: consent is false for '{name}' — not writing to storage")
            return "Not saved. The farmer has not agreed to be remembered, so nothing was written to storage."

        user_id = normalize_user_id(name)
        self._current_user_id = user_id
        self._farmer_name = name

        facts = {}
        if crops:
            facts["crops"] = crops
        if land_size:
            facts["land_size"] = land_size
        if district:
            facts["district"] = district
        if irrigation_type:
            facts["irrigation_type"] = irrigation_type
        if last_topic:
            facts["last_topic"] = last_topic

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

    @function_tool
    async def get_weather_forecast(self, context: RunContext, district: str):
        """Look up today's weather forecast for a district in India, using a live weather service.

        Call this whenever the farmer asks about weather, rain, temperature, or whether it's safe to sow, spray, or harvest today. If the farmer already told you their district earlier in this call or it's saved in their known details, use that district automatically instead of asking again — only ask for the district if you truly don't have one.

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
                f"expected rainfall {forecast['precipitation_mm']}mm. "
                "Tell the farmer this is today's forecast, mention the date, and remind them "
                "conditions can shift, so they should keep an eye on the sky too."
            )
        except WeatherLookupError as e:
            logger.warning(f"get_weather_forecast: failed for '{district}': {e}")
            self._outcome = "failure"
            self._reason = "weather_lookup_failed"
            return (
                "The weather lookup failed right now. Tell the farmer you couldn't fetch "
                "today's forecast, apologize briefly, and suggest they check a local weather "
                "app or the radio for now, rather than guessing the weather yourself. "
                "If they need a real answer and seem to want one, offer to create a human "
                "follow-up request using your escalation tool, with their consent."
            )

    @function_tool
    async def get_government_scheme_info(self, context: RunContext, scheme_query: str):
        """Look up information about Indian government schemes for farmers, from a local reference dataset.

        Call this whenever the farmer asks about a government scheme by name, or asks something like "is there any scheme for me" or "how can the government help me". You can search by scheme name (like "PM-KISAN") or by topic (like "insurance", "loan", "pension", "soil").

        Args:
            scheme_query: What the farmer is asking about — a scheme name or a topic like "insurance" or "loan".
        """
        matches = find_schemes(scheme_query)
        logger.info(f"get_government_scheme_info: query='{scheme_query}', matches={len(matches)}")

        if not matches:
            all_names = ", ".join(s["name"] for s in list_all_schemes())
            self._outcome = "failure"
            self._reason = "scheme_not_found"
            return (
                f"No scheme matched '{scheme_query}' in the local reference list. "
                f"Tell the farmer you don't have that specific one, mention the schemes you do "
                f"know about ({all_names}), and suggest they check with their local agriculture "
                "office or the nearest Common Service Centre for anything more specific."
            )

        self._outcome = "success"
        self._reason = "scheme_info_delivered"

        summary_parts = []
        for s in matches[:2]:
            summary_parts.append(
                f"{s['name']} ({s['full_name']}): {s['description']} "
                f"Eligibility — {s['eligibility']} How to apply — {s['how_to_apply']}"
            )

        return (
            " | ".join(summary_parts)
            + " This is general information from a reference list, not live government data — "
            "tell the farmer to confirm exact eligibility and current status with their local "
            "agriculture office or Common Service Centre before applying."
        )

    @function_tool
    async def create_escalation(
        self,
        context: RunContext,
        farmer_name: str,
        reason_category: str,
        summary: str,
        urgency: str,
        consent: bool,
        language: str | None = None,
        follow_up_method: str | None = None,
    ):
        """Create a request for a human to follow up with this farmer, only after they've agreed to it.

        Call this in exactly two situations: (1) the market price or weather data you needed is missing, unavailable, or clearly outdated and the farmer needs a real answer, or (2) the farmer describes a serious crop problem — something like widespread crop failure, a severe unexplained disease outbreak, or anything beyond simple pest/disease guidance.

        Before calling this, always tell the farmer in plain words what you want to send to a human (their name, a short summary of the problem, how urgent it seems) and ask if that's okay. Set consent to true only if they clearly agreed, false otherwise — if false, this function will not create anything.

        Never include passwords, OTPs, PINs, account numbers, or other sensitive personal information in the summary.

        Args:
            farmer_name: The farmer's name.
            reason_category: Either "missing_or_old_data" or "serious_crop_problem".
            summary: A short, factual summary (2-3 sentences) covering who needs help, what happened, and what you already checked or told them.
            urgency: One of "low", "medium", "high", or "emergency".
            consent: True only if the farmer clearly agreed to you sharing this, false otherwise.
            language: The language the farmer has been speaking in this call, e.g. "Hindi", "Hinglish", "English".
            follow_up_method: How the farmer prefers to be followed up with, if they said, e.g. "call back", "same number".
        """
        if not consent:
            logger.info(f"create_escalation: consent false for '{farmer_name}' — not creating")
            return "Not created. The farmer did not agree to share this with a human, so no request was made."

        escalation_id = db_create_escalation(
            farmer_name=farmer_name,
            reason_category=reason_category,
            summary=summary,
            urgency=urgency,
            language=language or "",
            follow_up_method=follow_up_method or "",
        )
        logger.info(f"create_escalation: created #{escalation_id} for '{farmer_name}' ({reason_category}, {urgency})")

        self._outcome = "success"
        self._reason = "escalation_created"

        return (
            f"Request created with reference ID {escalation_id}. Tell the farmer this reference number, "
            "and let them know a human from the local agriculture support team will follow up — "
            "do not promise a specific response time unless you actually know one."
        )

    @function_tool
    async def transfer_to_crop_specialist(self, context: RunContext):
        """Hand off the conversation to the crop problem specialist, for anything requiring deeper crop disease, pest, or crop-health troubleshooting than simple guidance.

        Call this when the farmer describes a specific crop health problem in detail and wants focused troubleshooting help — symptoms, likely causes, and what to try — beyond what a quick answer covers. Do not call this for simple factual questions like sowing time, weather, mandi prices, or schemes; the main agent handles those directly.

        Before calling this, tell the farmer in one short sentence that you're connecting them to the crop specialist. Do not ask permission — this is a normal, expected handoff, not a data-sharing action.
        """
        logger.info(f"transfer_to_crop_specialist: handing off for '{self._farmer_name or 'unknown'}'")
        return CropSpecialistAgent(main_assistant=self, farmer_name=self._farmer_name)


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    call_id = start_call(channel="browser")

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),
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

    @session.on("user_input_transcribed")
    def on_user_input_transcribed(ev: UserInputTranscribedEvent):
        transcript = ev.transcript.strip().lower()
        if not transcript:
            return

        has_devanagari = any(0x0900 <= ord(c) <= 0x097F for c in transcript)

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

    assistant = Assistant(call_id=call_id)

    async def on_shutdown():
        # Default to success if the call completed with no recorded error —
        # not every helpful turn goes through a tool (e.g. general farming
        # advice answered directly from the model's own knowledge), so the
        # absence of a tool-set outcome must not be read as failure.
        outcome = assistant._outcome or "success"
        reason = assistant._reason or "general_conversation"
        finish_call(call_id, outcome=outcome, reason=reason, farmer_name=assistant._farmer_name)
        logger.info(f"call #{call_id} finished: outcome={outcome}, reason={reason}")

    ctx.add_shutdown_callback(on_shutdown)

    await session.start(
        agent=assistant,
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

    await ctx.connect()

    await session.generate_reply(
        instructions="Greet the farmer warmly, introduce yourself as Kisan Sahay, ask their name and ask how you can help them today."
    )


if __name__ == "__main__":
    cli.run_app(server)