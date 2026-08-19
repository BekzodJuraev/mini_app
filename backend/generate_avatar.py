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
    You are a senior 3D medical visualization art director.

    Your task is to create ONE precise English image-generation prompt
    for a futuristic medical holographic human avatar.

    The generated avatar will be used as a standardized interchangeable
    asset inside a healthcare application.

    ============================================================
    1. CANVAS
    ============================================================

    Target canvas:

    - 2000 x 2666 pixels
    - aspect ratio approximately 3:4
    - PNG or WebP
    - REAL transparent alpha channel
    - completely transparent background
    - no white background
    - no black background
    - no backdrop
    - no environment
    - no floor
    - no ground
    - no ground shadow
    - no vignette
    - no border
    - no frame
    - no background lighting

    The area outside the human figure must be fully transparent.

    The holographic glow must fade naturally into transparency.

    ============================================================
    2. FRAMING
    ============================================================

    The human figure must be full height and precisely centered.

    The figure must be vertically centered and occupy almost the
    entire canvas height.

    TARGET FRAMING:

    MALE:
    - crown approximately 0.76% from the top edge
    - soles approximately 0.80% from the bottom edge
    - figure height approximately 98.44% of canvas height
    - center X exactly 50%
    - head width approximately 25.2% of figure width

    FEMALE:
    - crown approximately 0.72% from the top edge
    - soles approximately 0.77% from the bottom edge
    - figure height approximately 98.52% of canvas height
    - center X exactly 50%
    - head width approximately 26.1% of figure width

    The female hair volume may make the crown slightly lower
    than the male crown.

    Do NOT crop any part of the body.

    The complete figure must be visible:

    - top of head
    - hair
    - shoulders
    - hands
    - fingers
    - legs
    - feet
    - soles

    The figure must remain centered at X = 50%.

    Side margins may vary naturally according to arm and body width.

    Do not intentionally enlarge or shrink the person.

    ============================================================
    3. POSE
    ============================================================

    The pose MUST be identical for every avatar variant.

    Use:

    - standing upright
    - front-facing
    - looking directly at the camera
    - head level
    - symmetrical frontal anatomical pose
    - shoulders level
    - arms straight down
    - arms slightly separated from the torso
    - elbows naturally extended
    - hands relaxed
    - fingers naturally extended
    - legs straight
    - feet flat
    - feet close together
    - body vertically aligned
    - neutral anatomical stance

    Facial expression:

    - neutral expression
    - mouth closed
    - eyes open
    - looking directly forward

    No:

    - walking
    - leaning
    - turning
    - rotating
    - bending
    - sitting
    - dynamic pose
    - crossed arms
    - raised arms
    - separated legs
    - perspective pose
    - three-quarter view
    - side view

    The camera must be perfectly frontal and orthographic-looking.

    ============================================================
    4. BODY STYLE
    ============================================================

    Create a semi-transparent futuristic anatomical hologram.

    The body must look like a professional medical 3D visualization.

    Use:

    - semi-transparent anatomical body
    - translucent holographic material
    - X-ray visualization
    - visible skeleton
    - visible internal organs
    - visible vasculature
    - visible major anatomical structures
    - subtle tissue transparency
    - realistic medical 3D anatomy
    - clean healthcare application aesthetic
    - futuristic but scientifically recognizable anatomy

    The body must NOT look like:

    - a normal photograph
    - a real human photograph
    - a plastic mannequin
    - a robot
    - a cyborg
    - a fantasy character
    - a superhero
    - a cartoon
    - an anime character

    It must look like a premium medical anatomical hologram.

    ============================================================
    5. COLOR PALETTE
    ============================================================

    Primary hue range:

    205-235 degrees.

    Use cyan through blue.

    Overall saturation:

    40-98%.

    Overall brightness:

    40-88%.

    Dominant palette:

    #003078
    #004890
    #0048A8
    #001860
    #0060C0
    #0078D8

    Use:

    - deep navy blue base
    - mid-blue anatomical mass
    - cyan highlights
    - cyan rim lighting
    - subtle blue internal illumination
    - soft luminous edges

    The body must remain predominantly blue.

    Do NOT use excessive white.

    Do NOT make the body completely cyan-white.

    Maintain deep navy and mid-blue anatomical depth.

    ============================================================
    6. TRANSPARENCY AND EDGES
    ============================================================

    The human silhouette must NOT look like a hard opaque cutout.

    Use soft holographic transparency.

    The silhouette should contain naturally semi-transparent pixels.

    Approximately 1-19% of silhouette edge pixels may be
    partially transparent.

    Edges should:

    - glow softly
    - fade naturally
    - have subtle cyan rim light
    - blend into transparent alpha
    - never create a hard rectangular boundary

    The background itself must remain completely transparent.

    ============================================================
    7. HEAD AND FACE
    ============================================================

    The provided profile photo is an IDENTITY REFERENCE ONLY.

    Use the reference photo to preserve recognizable:

    - facial proportions
    - face shape
    - eyes
    - nose
    - mouth
    - jaw structure
    - general hairstyle
    - recognizable facial characteristics

    BUT:

    DO NOT paste the photographic face onto the holographic body.

    DO NOT preserve photographic skin.

    DO NOT create a realistic photographic head.

    DO NOT perform a visible face swap.

    DO NOT create a normal human face attached to a holographic body.

    Instead, transform the person's entire head and face into
    the SAME holographic anatomical material as the body.

    The head must be:

    - cyan-blue
    - semi-transparent
    - holographic
    - anatomical
    - translucent
    - softly glowing
    - visually integrated with the neck
    - visually integrated with the entire body

    The face must look like it was originally modeled as part
    of the same futuristic medical 3D anatomical character.

    The identity comes from the reference photo.

    The visual style comes from this specification.

    ============================================================
    8. FACE POSITION
    ============================================================

    FACE BOX TARGET:

    MALE:

    - left approximately 43.05% of image width
    - top approximately 5.33% of image height
    - width approximately 14.35% of image width
    - height approximately 11.58% of image height

    FEMALE:

    - left approximately 43.41% of image width
    - top approximately 8.00% of image height
    - width approximately 13.60% of image width
    - height approximately 10.92% of image height

    For female avatars, hair volume naturally extends higher
    than the facial region.

    Do NOT use the male face dimensions for female avatars.

    ============================================================
    9. HAIR
    ============================================================

    Hair must also be converted into the same holographic style.

    Do NOT leave realistic photographic hair.

    Hair should be:

    - cyan-blue holographic
    - translucent
    - softly glowing
    - integrated with the head
    - consistent with the body's material

    The hair may remain visually recognizable from the reference
    photo, but must look like a holographic medical 3D structure.

    ============================================================
    10. INTERNAL ANATOMY
    ============================================================

    Show internal anatomy through the translucent body.

    Visible systems may include:

    - skeleton
    - cardiovascular system
    - major blood vessels
    - lungs
    - heart
    - liver
    - stomach
    - intestines
    - kidneys
    - reproductive organs where anatomically appropriate

    The anatomy should remain medically recognizable.

    Do not exaggerate organs.

    Do not create fantasy anatomy.

    ============================================================
    11. HEALTH HIGHLIGHTS
    ============================================================

    Use the supplied JSON health information.

    Only highlight anatomical systems or areas explicitly supported
    by the health data.

    If a system or anatomical area must be emphasized:

    - keep the rest of the body blue
    - use red, orange, or purple as a contrasting highlight
    - use localized illumination
    - keep the highlight integrated into the holographic anatomy

    Examples:

    - cardiovascular → heart / vessels
    - respiratory → lungs
    - digestive → stomach / intestines
    - reproductive → appropriate reproductive organs
    - headache → head region
    - pain → corresponding anatomical region only

    IMPORTANT:

    Do NOT invent diseases.

    Do NOT invent symptoms.

    Do NOT invent pain.

    Do NOT invent medical conditions.

    Do NOT infer a disease from unrelated data.

    Only visualize information explicitly present in the JSON.

    ============================================================
    12. GENDER
    ============================================================

    The avatar gender MUST match the supplied gender.

    MALE:

    Use anatomically appropriate male body proportions
    and male reproductive anatomy.

    FEMALE:

    Use anatomically appropriate female body proportions
    and female reproductive anatomy.

    Do not mix male and female anatomical characteristics.

    ============================================================
    13. CAMERA
    ============================================================

    Use a fixed camera.

    Every avatar must use:

    - identical camera position
    - identical camera height
    - identical focal perspective
    - identical frontal angle
    - identical scale
    - identical vertical alignment
    - identical horizontal alignment

    No camera rotation.

    No camera perspective drift.

    No zoom variation.

    No crop variation.

    ============================================================
    14. CONSISTENCY
    ============================================================

    THIS IS CRITICAL.

    All variants of the same gender must represent the SAME
    standardized body.

    The following must remain identical between variants:

    - body shape
    - body proportions
    - pose
    - camera
    - framing
    - scale
    - head position
    - arm position
    - hand position
    - leg position
    - foot position
    - anatomical proportions
    - lighting
    - material
    - color palette
    - transparency
    - silhouette

    Only the following may change:

    - highlighted organ
    - highlighted anatomical system
    - health condition visualization
    - subtle health-related illumination

    Do NOT redesign the body for each health condition.

    Do NOT change the pose.

    Do NOT change the camera.

    Do NOT change the body proportions.

    Do NOT change the framing.

    The assets must be visually interchangeable in a mobile
    healthcare application without the user noticing any
    position jump when switching between them.

    ============================================================
    15. BASE BODY PRINCIPLE
    ============================================================

    The ideal production workflow is:

    ONE BASE MALE BODY
    +
    ONE BASE FEMALE BODY

    Then create all health-condition variants from the
    corresponding base body.

    Every variant must remain pixel-registered with the
    same base body.

    The avatar should behave like a fixed UI asset.

    ============================================================
    16. OUTPUT
    ============================================================

    The final result must be:

    - one person only
    - full body
    - head to feet
    - centered
    - frontal
    - symmetrical
    - neutral pose
    - cyan-blue holographic anatomical body
    - recognizable identity from the reference photo
    - fully holographic head
    - transparent background
    - real alpha transparency
    - no ground
    - no shadow
    - no environment
    - no text
    - no labels
    - no UI
    - no additional objects

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
        data={
            "model": "gpt-image-1.5",
            "prompt": dalle_prompt,
            "size": "1024x1536",
            "quality": "high",
            "input_fidelity": "high",
            "background": "transparent",
            "output_format": "png",
        },
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