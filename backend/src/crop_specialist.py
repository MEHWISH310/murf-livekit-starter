import logging

from livekit.agents import Agent, function_tool, RunContext

from prompt import CROP_SPECIALIST_PROMPT

logger = logging.getLogger("crop-specialist")


class CropSpecialistAgent(Agent):
    def __init__(self, main_assistant, farmer_name: str = "") -> None:
        context_note = ""
        if farmer_name:
            context_note = (
                f"\n\nThe farmer's name is {farmer_name}, already known from earlier in this call — "
                "do not ask for it again."
            )
        super().__init__(instructions=CROP_SPECIALIST_PROMPT + context_note)
        self._main_assistant = main_assistant

    async def on_enter(self) -> None:
        await self.session.generate_reply(
            instructions=(
                "Introduce yourself in one short sentence as the crop problem specialist Kisan Sahay "
                "just connected the farmer to, then ask them to describe the crop problem in detail "
                "if they haven't already fully described it. "
                "Reply in exactly the same language and script as the farmer's most recent message "
                "in the conversation so far — if they were speaking English, reply fully in English; "
                "if Hindi or Hinglish, reply in Devanagari Hindi. Do not default to Hindi just because "
                "you are the specialist."
            )
        )

    @function_tool
    async def transfer_back_to_kisan_sahay(self, context: RunContext):
        """Hand the conversation back to the main Kisan Sahay assistant.

        Call this once the crop problem has been discussed and you've given your guidance, or if the farmer asks about something outside crop troubleshooting, like weather, mandi prices, or government schemes. Before calling this, tell the farmer in one short sentence that you're connecting them back to Kisan Sahay.
        """
        logger.info("transfer_back_to_kisan_sahay: handing back to main assistant")
        return self._main_assistant