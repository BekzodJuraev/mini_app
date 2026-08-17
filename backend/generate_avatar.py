import openai
import base64
import json
import requests
import mimetypes

from config import KEY, MODEL


openai.api_key = KEY

OPENAI_API_URL = "https://api.openai.com/v1"


def generate_direct_dalle_avatar(
    user_data_payload: dict,
    gender: str = "female",
    profile_photo=None,
) -> bytes:
    """
    GPT → English prompt → GPT Image 1.5 + profile photo → PNG bytes
    """

    if not profile_photo:
        raise ValueError("Profile photo is required")

    # ==========================================================
    # 1. GPT → generate image prompt
    # ==========================================================

    system_prompt = """
You are a visual art director specializing in futuristic
3D medical visualization.

Create an English prompt for an AI image generator.

The provided photo is ONLY an identity reference.

The reference photo should be used to understand the person's
facial characteristics, facial proportions, hairstyle and
overall identity.

IMPORTANT:

Do NOT paste the original photographic face onto the body.

Do NOT create a realistic photographic human head.

Do NOT make the result look like a face swap.

Do NOT preserve realistic skin texture.

Instead, completely transform the person's head and face
into the SAME futuristic cyan-blue holographic anatomical
material and rendering style as the rest of the body.

The head, face, neck and body must look like ONE single
unified 3D medical hologram.

==========================================================
HEAD AND FACE
==========================================================

The person's facial identity should be recognizable from
the reference photo, but the entire head must be converted
into a futuristic holographic anatomical 3D representation.

The head must have:

- cyan-blue holographic appearance
- semi-transparent material
- translucent anatomical facial structures
- subtle visible facial bones
- subtle anatomical structures beneath the face
- glowing cyan-blue edges
- soft holographic illumination
- futuristic medical visualization
- facial proportions inspired by the reference photo
- recognizable facial characteristics from the reference
- same material and rendering style as the body

The face must NOT look photographic.

No realistic skin.

No photographic texture.

No pasted face.

No face swap appearance.

No sharp boundary between the real face and holographic body.

The head must visually belong to the same holographic anatomical
character as the entire body.

==========================================================
BODY
==========================================================

Create one human full-body avatar.

The entire body must be visible from the top of the head
to the bottom of the feet.

The character must be:

- standing
- facing directly toward the camera
- centered
- symmetrical frontal view
- neutral anatomical pose
- arms naturally positioned beside the body
- both legs fully visible
- both feet fully visible

The entire body must be a futuristic cyan-blue holographic
medical 3D render.

Use:

- semi-transparent x-ray anatomical body
- visible skeleton
- visible blood vessels
- visible internal organs
- glowing internal organ systems
- translucent anatomical structures
- cyan-blue luminous edges
- realistic medical 3D rendering
- clean professional healthcare application style

The head must use EXACTLY the same holographic material
and visual treatment as the body.

The entire person must look like one single 3D render.

==========================================================
VISUAL STYLE
==========================================================

The final image should resemble a futuristic medical
anatomical hologram.

Use:

- cyan-blue holographic color
- translucent body
- glowing anatomical structures
- subtle volumetric glow
- realistic 3D medical visualization
- high-quality 3D rendering
- clean professional healthcare application aesthetic

Background:

- solid pitch-black background
- completely black
- no environment
- no room
- no furniture
- no objects
- no shadows from an environment

==========================================================
COMPOSITION
==========================================================

Vertical composition.

Full body must fit inside the image.

Leave a small amount of empty space above the head
and below the feet.

Do not crop:

- head
- hair
- shoulders
- hands
- legs
- feet

The person must occupy most of the vertical frame.

No additional people.

No text.

No labels.

No UI.

No medical interface.

==========================================================
HEALTH VISUALIZATION
==========================================================

Use the health information from the JSON to create subtle
visual highlights.

If a health problem is explicitly present in the JSON,
highlight only the corresponding anatomical area using
red, orange, or purple light.

The highlighted area should remain integrated with the
cyan-blue holographic body.

Do NOT invent diseases.

Do NOT invent symptoms.

Do NOT invent pain.

Do NOT invent medical conditions.

Only visualize problems explicitly present in the JSON.

==========================================================
MOST IMPORTANT REQUIREMENT
==========================================================

The reference photo provides the person's identity.

The reference photo does NOT provide the final visual style.

Transform the entire person into a single futuristic
cyan-blue holographic anatomical medical avatar.

The person's facial characteristics should influence
the generated holographic face.

However, the final head must NOT look like a normal
photographic human head.

The head must look like it was originally created as
part of the same holographic anatomical 3D model.

The final result should look like:

ONE PERSON
+
ONE UNIFIED HOLOGRAPHIC ANATOMICAL BODY
+
ONE UNIFIED HOLOGRAPHIC ANATOMICAL HEAD

Everything must have the same cyan-blue holographic
material and lighting.

Return ONLY the final English image-generation prompt.
"""

    gpt_response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": (
                    f"Gender: {gender}\n"
                    f"Health data:\n"
                    f"{json.dumps(user_data_payload, ensure_ascii=False, default=str)}"
                ),
            },
        ],
        temperature=0.3,
    )

    dalle_prompt = (
        gpt_response
        .choices[0]
        .message
        .content
        .strip()
        .strip('"')
    )

    if not dalle_prompt:
        raise ValueError("GPT returned empty image prompt")

    # ==========================================================
    # 2. Read profile.photo
    # ==========================================================

    profile_photo.open("rb")

    try:
        photo_bytes = profile_photo.read()
        photo_name = profile_photo.name
    finally:
        profile_photo.close()

    if not photo_bytes:
        raise ValueError("Profile photo is empty")

    # ==========================================================
    # 3. Determine MIME type
    # ==========================================================

    mime_type, _ = mimetypes.guess_type(photo_name)

    if not mime_type:
        mime_type = "image/jpeg"

    # ==========================================================
    # 4. GPT Image 1.5
    # ==========================================================

    headers = {
        "Authorization": f"Bearer {KEY}",
    }

    files = {
        "image[]": (
            photo_name,
            photo_bytes,
            mime_type,
        ),
    }

    data = {
        "model": "gpt-image-1.5",

        "prompt": dalle_prompt,

        "n": 1,

        # Vertical because we need full body
        "size": "1024x1536",

        "quality": "high",

        # High fidelity helps preserve facial characteristics
        "input_fidelity": "high",

        # We want black background
        "background": "opaque",

        # Return PNG
        "output_format": "png",
    }

    image_response = requests.post(
        f"{OPENAI_API_URL}/images/edits",
        headers=headers,
        data=data,
        files=files,
        timeout=300,
    )

    # ==========================================================
    # 5. Handle API error
    # ==========================================================

    if image_response.status_code != 200:

        try:
            error_data = image_response.json()
        except Exception:
            error_data = image_response.text

        raise RuntimeError(
            f"GPT Image generation failed "
            f"({image_response.status_code}): {error_data}"
        )

    image_data = image_response.json()

    # ==========================================================
    # 6. Base64 → PNG bytes
    # ==========================================================

    try:
        image_base64 = image_data["data"][0]["b64_json"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(
            f"Invalid GPT Image response: {image_data}"
        ) from exc

    try:
        image_bytes = base64.b64decode(image_base64)
    except Exception as exc:
        raise RuntimeError(
            "Failed to decode generated image"
        ) from exc

    if not image_bytes:
        raise RuntimeError("Generated image is empty")

    return image_bytes