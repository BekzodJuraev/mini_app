import base64
import mimetypes
import requests

from config import KEY


OPENAI_API_URL = "https://api.openai.com/v1"


BASE_PROMPT = """
You are generating a standardized medical holographic avatar for a healthcare application.

CANVAS:
- 2000 x 2666 px
- aspect ratio 3:4
- PNG with real alpha transparency
- completely transparent background
- no backdrop
- no floor
- no shadow
- no vignette
- no border

FRAMING:
- full-height human figure
- perfectly centered
- center X = 50%
- male crown approximately 0.76% from top
- female crown approximately 0.72% from top
- male soles approximately 0.80% from bottom
- female soles approximately 0.77% from bottom
- figure height approximately 98.5% of canvas
- do not crop any part of the body

POSE:
- standing
- front-facing
- symmetrical
- head level
- looking directly at camera
- arms straight down and slightly separated from torso
- legs straight
- feet flat and close together
- neutral expression
- mouth closed
- eyes open
- full body from crown to soles

MALE:
- short hair
- male body proportions
- flat chest
- male hip and shoulder proportions

FEMALE:
- long hair falling behind shoulders
- breasts present
- female hip and shoulder proportions

STYLE:
- semi-transparent anatomical hologram
- medical 3D visualization
- X-ray style
- visible internal anatomy
- visible skeleton and vasculature
- futuristic healthcare application aesthetic
- scientifically recognizable anatomy

COLOR:
- cyan through blue
- hue 195-225 degrees
- deep navy blue base
- mid-blue anatomical mass
- cyan highlights
- cyan rim light
- soft luminous edges
- dominant colors:
  #003078
  #004890
  #0048A8
  #001860
  #0060C0
  #0078D8

The silhouette must have soft holographic transparency.
Do not create a hard opaque cutout.

IMPORTANT:
All six system avatars of the same gender must use the SAME:
- body
- body proportions
- pose
- camera
- framing
- scale
- silhouette
- head position
- arm position
- leg position
- lighting
- material

Only the highlighted anatomical system may differ.

Do not add:
- text
- labels
- arrows
- UI
- watermark
- additional people
- additional objects
- environment
"""


SYSTEM_PROMPTS = {
    "cardiovascular": """
EMPHASIZE THE CARDIOVASCULAR SYSTEM.

HIGHLIGHTED:
- Heart centered in the chest and slightly left.
- Heart is the focal point.
- Complete arterial tree from the aortic arch through carotids,
  arms, abdominal aorta, iliac arteries, femoral arteries and feet.
- Venous tree running alongside arteries.
- Vessels must be continuous from head to toes.

ACCENT:
- Male heart and arteries: #79081E -> #84123F
- Male veins: #7D2E78
- Female heart and arteries: #FC5F5E
- Female veins: #AF439D

SUPPRESS:
- lungs
- digestive organs
- skeleton

The cardiovascular system must clearly dominate the image.
""",

    "digestive": """
EMPHASIZE THE DIGESTIVE SYSTEM.

HIGHLIGHTED IN BRIGHT CYAN-WHITE:
- oral cavity and tongue
- pharynx
- oesophagus
- stomach
- liver edge
- gallbladder
- small intestine
- large intestine
- rectum

The digestive tract must be the brightest anatomical structure.

Use:
#7FE3FF
through
#E5EFF6

Add a soft cyan bloom.

SUPPRESS:
- heart
- lungs
- skeleton
- vessels

Keep all other structures deep blue and dim.
""",

    "endocrine": """
EMPHASIZE THE ENDOCRINE SYSTEM.

Highlight the following glands in warm orange-coral:

- hypothalamus
- pituitary gland
- thyroid
- parathyroids
- both adrenal glands
- pancreas

MALE:
- testes

FEMALE:
- ovaries
- uterus

MALE ACCENTS:
#CE6848
#D37E51
#D0767A

FEMALE ACCENTS:
#FFC8B2
#E4A1B7
#B7698B

Each gland must have a small soft halo so it remains visible.

All other anatomy remains faint blue.

Nothing else may use warm colors.
""",

    "musculoskeletal": """
EMPHASIZE THE SKELETAL SYSTEM.

HIGHLIGHT:
- skull
- orbits
- jaw
- cervical spine
- thoracic spine
- lumbar spine
- complete ribcage
- sternum
- clavicles
- scapulae
- pelvis
- every limb bone
- hands
- feet

Joints should be slightly brighter than bone shafts.

Use:
#E6EEF6

No warm colors.

SUPPRESS:
- all internal organs
- blood vessels

Only the dark translucent body silhouette remains around the skeleton.

IMPORTANT:
Show bones only.
Do NOT emphasize muscles.
""",

    "respiratory": """
EMPHASIZE THE RESPIRATORY SYSTEM.

HIGHLIGHT:
- nasal cavity
- pharynx
- trachea
- bronchial tree
- both lungs
- clearly separated lung lobes

The trachea must descend through the center of the neck.
The bronchial tree must branch naturally into both lungs.

Use:
#7FE3FF
through
#E7EEF5

Add a soft cyan bloom around the lungs.

SUPPRESS:
- heart
- abdominal organs
- skeleton

For female anatomy, lungs must remain clearly visible behind the breast tissue.
""",

    "reproductive": """
EMPHASIZE THE REPRODUCTIVE SYSTEM.

MALE:
Highlight:
- prostate
- seminal vesicles
- vas deferens
- testes
- penis

Use:
#7561B6
#C0A8EF

FEMALE:
Highlight:
- uterus
- both fallopian tubes
- both ovaries
- vagina

Use:
#B7A8FF
#C8B2F3

The reproductive organs must glow in violet-magenta.

SUPPRESS:
- abdominal organs
- pelvis outline

Nothing above the waist should be emphasized.
""",
}


def generate_system_avatars(profile):
    """
    Generates all 6 standardized system avatars.

    Arguments:
        profile.photo
        profile.gender

    Returns:
        {
            "cardiovascular": bytes,
            "digestive": bytes,
            "endocrine": bytes,
            "musculoskeletal": bytes,
            "respiratory": bytes,
            "reproductive": bytes,
        }
    """

    if not profile.photo:
        raise ValueError("Profile photo is required")

    gender = profile.gender.lower()

    if gender not in ("male", "female"):
        raise ValueError("Gender must be 'male' or 'female'")

    # --------------------------------------------------
    # Read profile photo once
    # --------------------------------------------------

    profile.photo.open("rb")

    try:
        photo_bytes = profile.photo.read()
        photo_name = profile.photo.name
    finally:
        profile.photo.close()

    if not photo_bytes:
        raise ValueError("Profile photo is empty")

    mime_type, _ = mimetypes.guess_type(photo_name)
    mime_type = mime_type or "image/jpeg"

    files = {
        "image[]": (
            photo_name,
            photo_bytes,
            mime_type,
        )
    }

    headers = {
        "Authorization": f"Bearer {KEY}",
    }

    result = {}

    # --------------------------------------------------
    # Generate 6 systems
    # --------------------------------------------------

    for system_name, system_prompt in SYSTEM_PROMPTS.items():

        gender_specific = f"""
GENDER:
{gender.upper()}

The generated person MUST match this gender.

{system_prompt}
"""

        final_prompt = (
            BASE_PROMPT
            + "\n"
            + gender_specific
        )

        response = requests.post(
            f"{OPENAI_API_URL}/images/edits",
            headers=headers,
            data={
                "model": "gpt-image-1.5",
                "prompt": final_prompt,
                "size": "1024x1536",
                "quality": "high",
                "input_fidelity": "high",
                "background": "transparent",
                "output_format": "png",
            },
            files=files,
            timeout=300,
        )

        if response.status_code != 200:
            try:
                error_data = response.json()
            except Exception:
                error_data = response.text

            raise RuntimeError(
                f"Failed to generate {system_name} avatar "
                f"({response.status_code}): {error_data}"
            )

        response_data = response.json()

        try:
            image_base64 = response_data["data"][0]["b64_json"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(
                f"Invalid response for {system_name}: "
                f"{response_data}"
            ) from exc

        try:
            image_bytes = base64.b64decode(image_base64)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to decode {system_name} avatar"
            ) from exc

        if not image_bytes:
            raise RuntimeError(
                f"Generated {system_name} avatar is empty"
            )

        result[system_name] = image_bytes

    return result