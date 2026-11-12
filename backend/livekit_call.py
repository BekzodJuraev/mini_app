from datetime import timedelta

from livekit import api
from config import LIVEKIT_URL,LIVEKIT_API_KEY,LIVEKIT_API_SECRET

def generate_livekit_token(room_name: str, identity: str, participant_name: str) -> str:
    """
    Генерирует JWT-токен LiveKit для аудиозвонка в комнате room_name.
    """
    token = (
        api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(identity)
        .with_name(participant_name)
        .with_ttl(timedelta(hours=1))
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        )
    )
    return token.to_jwt()