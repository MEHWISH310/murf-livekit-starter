import argparse
import asyncio
import json
import os
import uuid

from dotenv import load_dotenv
from livekit import api

load_dotenv(".env.local")

AGENT_NAME = "kisan-sahay-outbound"


async def main(to: str, farmer_name: str, district: str):
    lkapi = api.LiveKitAPI(
        url=os.environ["LIVEKIT_URL"],
        api_key=os.environ["LIVEKIT_API_KEY"],
        api_secret=os.environ["LIVEKIT_API_SECRET"],
    )

    room_name = f"outbound-{uuid.uuid4().hex[:8]}"
    trunk_id = os.environ["LIVEKIT_SIP_OUTBOUND_TRUNK_ID"]
    metadata = json.dumps({"farmer_name": farmer_name, "district": district})

    print(f"Dispatching agent to room {room_name} ...")
    await lkapi.agent_dispatch.create_dispatch(
        api.CreateAgentDispatchRequest(
            agent_name=AGENT_NAME,
            room=room_name,
            metadata=metadata,
        )
    )

    print(f"Dialing {to} ...")
    await lkapi.sip.create_sip_participant(
        api.CreateSIPParticipantRequest(
            sip_trunk_id=trunk_id,
            sip_call_to=to,
            room_name=room_name,
            participant_identity=f"caller-{to}",
            participant_name=farmer_name or "Farmer",
            wait_until_answered=True,
        )
    )

    print("Call answered — agent should be speaking now.")
    await lkapi.aclose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--to", required=True, help="Linphone username to call, e.g. mehwish310")
    parser.add_argument("--name", default="", help="Farmer's name")
    parser.add_argument("--district", default="", help="Farmer's district, for the weather check")
    args = parser.parse_args()

    asyncio.run(main(args.to, args.name, args.district))