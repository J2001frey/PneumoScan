"""Claude API integration: turns the CNN output into a plain-language explanation."""
import logging

from anthropic import Anthropic, APIError

from app.config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from app.prompts import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)
_client: Anthropic | None = None


def _get_client() -> Anthropic | None:
    global _client
    if not ANTHROPIC_API_KEY:
        return None
    if _client is None:
        _client = Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def _fallback_explanation(pred: dict) -> str:
    label, conf = pred["label"], pred["confidence"]
    finding = ("a pattern the model associates with pneumonia"
               if label == "PNEUMONIA" else "no pneumonia-like pattern")
    caution = " The model is not very certain, so treat this result with extra caution." \
        if pred["low_confidence"] else ""
    return (f"The model detected {finding} (confidence {conf:.0%}).{caution} "
            "This is an automated screening aid and can be wrong. "
            "Please have a qualified clinician review the original image.")


def generate_explanation(pred: dict) -> str:
    """Return Claude's explanation, or a safe template if the API is unavailable."""
    client = _get_client()
    if client is None:
        logger.warning("ANTHROPIC_API_KEY not set; using fallback explanation.")
        return _fallback_explanation(pred)

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image",
                     "source": {"type": "base64", "media_type": "image/png",
                                "data": pred["heatmap_base64"]}},
                    {"type": "text",
                     "text": build_user_prompt(pred["label"], pred["confidence"],
                                               pred["probabilities"], pred["low_confidence"])},
                ],
            }],
        )
        text = "".join(b.text for b in response.content if b.type == "text").strip()
        return text or _fallback_explanation(pred)
    except APIError as exc:
        logger.error("Claude API error: %s", exc)
        return _fallback_explanation(pred)
    except Exception as exc:  # network errors etc. must never break /predict
        logger.error("Unexpected error calling Claude: %s", exc)
        return _fallback_explanation(pred)
