"""Local Ollama support for predictive-maintenance reports."""

from functools import lru_cache
import json

import ollama

OLLAMA_MODEL = "llama3.2"


class OllamaServerUnavailableError(RuntimeError):
    """Raised when the local Ollama server cannot be reached."""


class OllamaModelNotFoundError(RuntimeError):
    """Raised when the configured Ollama model is unavailable."""


def check_ollama_status() -> tuple[bool, str]:
    """Return whether the local briefing model is ready, plus a short status message."""
    try:
        models = ollama.list()
    except Exception:
        return False, "Ollama is not running. Start it, then click Generate AI briefing."

    names: list[str] = []
    model_entries = getattr(models, "models", None) or models.get("models", [])  # type: ignore[union-attr]
    for entry in model_entries:
        name = getattr(entry, "model", None) or getattr(entry, "name", None)
        if name is None and isinstance(entry, dict):
            name = entry.get("model") or entry.get("name")
        if name:
            names.append(str(name))

    if any(name.startswith(OLLAMA_MODEL) for name in names):
        return True, f"Local model ready: {OLLAMA_MODEL}"
    return False, f"Model {OLLAMA_MODEL} not found. Run: ollama pull {OLLAMA_MODEL}"


def generate_ai_report(machine_data: dict) -> str:
    """Generate a detailed maintenance report, reusing reports for the same data."""
    # A selected machine's readings do not change during a dashboard session.
    # Caching avoids another local-model inference when the button is clicked again.
    machine_json = json.dumps(machine_data, sort_keys=True, default=str)
    return _generate_ai_report(machine_json)


def generate_maintenance_briefing(recommendations: list[dict]) -> str:
    """Create an AI executive briefing from the current recommendation list."""
    recommendation_json = json.dumps(recommendations, sort_keys=True, default=str)
    return _generate_maintenance_briefing(recommendation_json)


@lru_cache(maxsize=256)
def _generate_ai_report(machine_json: str) -> str:
    """Run the model once for a unique set of machine readings."""
    machine_data = json.loads(machine_json)
    prompt = f"""
You are a predictive maintenance specialist. Create a concise, professional report
for the industrial machine below. Base your conclusions only on the supplied data.

Machine data:
- Product ID: {machine_data['Product ID']}
- Machine Type: {machine_data['Type']}
- Air Temperature: {machine_data['Air temperature [K]']} K
- Process Temperature: {machine_data['Process temperature [K]']} K
- Rotational Speed: {machine_data['Rotational speed [rpm]']} rpm
- Torque: {machine_data['Torque [Nm]']} Nm
- Tool Wear: {machine_data['Tool wear [min]']} min
- Machine Failure: {machine_data['Machine failure']}
- Tool Wear Failure: {machine_data['TWF']}
- Heat Dissipation Failure: {machine_data['HDF']}
- Power Failure: {machine_data['PWF']}
- Overstrain Failure: {machine_data['OSF']}
- Random Failure: {machine_data['RNF']}

Write a detailed professional maintenance summary in 3–4 connected paragraphs,
around 280–360 words total. Do not use headings, bullets, numbering, or lists.

In natural paragraph form, explain the machine's present condition and the important
sensor readings; clearly state whether a failure is present and its likely cause; assess
the operational risk and any immediate safety action; then give specific, practical
maintenance steps for the technician, including checks, repair or replacement work,
and a follow-up inspection plan. State a clear priority level and an appropriate
maintenance timeframe. For a healthy machine, clearly state that no corrective work
order is required, while still suggesting sensible preventive monitoring. Base every
statement only on the supplied machine data.
""".strip()

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            think=False,
            options={
                "temperature": 0.2,
                "num_predict": 520,
                "num_ctx": 2048,
            },
            keep_alive="30m",
        )
    except Exception as exc:
        message = str(exc).lower()
        if "connect" in message or "connection" in message or "refused" in message:
            raise OllamaServerUnavailableError("Ollama server is not running.") from exc
        if ("not found" in message or "404" in message) and "model" in message:
            raise OllamaModelNotFoundError(f"{OLLAMA_MODEL} model not found.") from exc
        raise

    report = response.message.content.strip()
    if not report:
        raise RuntimeError("Ollama returned an empty report.")
    return report


@lru_cache(maxsize=64)
def _generate_maintenance_briefing(recommendation_json: str) -> str:
    """Ask the local model to summarize and sequence maintenance actions."""
    prompt = f"""
You are a maintenance operations advisor speaking to a plant supervisor.
Based only on the recommendation data below, write a concise operational briefing
of 120-180 words.

Requirements:
- Start with the single most urgent action and who owns it.
- Then cover the next 2-3 priorities in plain language.
- End with one practical next step for the shift (for example, escalate, prepare parts, or generate a preventive work order).
- Do not invent sensor readings, failures, costs, dates, people, or facts not present in the data.
- Use short paragraphs only. No headings, bullets, or numbering.

Recommendation data:
{recommendation_json}
""".strip()
    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            think=False,
            options={"temperature": 0.2, "num_predict": 280, "num_ctx": 2048},
            keep_alive="30m",
        )
    except Exception as exc:
        message = str(exc).lower()
        if "connect" in message or "connection" in message or "refused" in message:
            raise OllamaServerUnavailableError("Ollama server is not running.") from exc
        if ("not found" in message or "404" in message) and "model" in message:
            raise OllamaModelNotFoundError(f"{OLLAMA_MODEL} model not found.") from exc
        raise

    briefing = response.message.content.strip()
    if not briefing:
        raise RuntimeError("Ollama returned an empty briefing.")
    return briefing
