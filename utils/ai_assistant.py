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
    """Create a consistently structured report matching the exact requested 4-image format."""
    machine_data = json.loads(machine_json)
    product_id = machine_data["Product ID"]
    failure_types = [
        label
        for label, flag in [
            ("Tool Wear Failure", "TWF"),
            ("Heat Dissipation Failure", "HDF"),
            ("Power Failure", "PWF"),
            ("Overstrain Failure", "OSF"),
            ("Random Failure", "RNF"),
        ]
        if machine_data[flag]
    ]
    failure_detected = bool(machine_data["Machine failure"])
    tool_wear = machine_data["Tool wear [min]"]
    air_temp = machine_data["Air temperature [K]"]
    proc_temp = machine_data["Process temperature [K]"]
    rot_speed = machine_data["Rotational speed [rpm]"]
    torque = machine_data["Torque [Nm]"]
    m_type = machine_data["Type"]

    if failure_detected:
        failure_status = ", ".join(failure_types) if failure_types else "Detected"
        failure_analysis = (
            f"Based on the provided data, a machine failure has been detected: {failure_status}. "
            f"The tool wear time is {tool_wear} minutes."
        )
        root_cause = (
            f"The root cause identified from the data is {failure_status}. "
            f"Machine operational parameters exceed acceptable thresholds during load."
        )
        risk_level = (
            f"Based on the data, the risk level is High. Reported failure: {failure_status}."
        )
        recommendation = (
            "Immediate corrective maintenance is recommended. Inspect and replace damaged tooling or components "
            "before placing the machine back into service."
        )
        preventive_actions = [
            "Perform immediate corrective maintenance and inspect damaged tooling/components.",
            "Monitor tool wear time closely and perform regular maintenance checks to ensure optimal machine performance.",
        ]
        conclusion = (
            f"Based on the provided machine data, Machine {product_id} requires immediate maintenance action due to a detected failure ({failure_status}). "
            "Following preventive and corrective protocols will restore optimal machine performance."
        )
    elif tool_wear >= 180:
        failure_status = "None (Elevated Tool Wear)"
        failure_analysis = (
            f"Based on the provided data, there are no reported failures. However, the tool wear time is {tool_wear} minutes, "
            "which approaches operational limits."
        )
        root_cause = (
            f"Elevated tool wear time of {tool_wear} minutes is the primary indicator requiring attention. No failure indicator is active."
        )
        risk_level = (
            f"Based on the data, the risk level is Medium. There are no reported failures, but tool wear time ({tool_wear} min) is elevated."
        )
        recommendation = (
            "Schedule a tool inspection and planned tool replacement during the next maintenance window."
        )
        preventive_actions = [
            "Monitor tool wear time closely to prevent excessive wear.",
            "Perform regular maintenance checks to ensure optimal machine performance.",
        ]
        conclusion = (
            f"Based on the provided machine data, Machine {product_id} is operating safely but with elevated tool wear ({tool_wear} min). "
            "Monitoring and planned tool replacement will ensure optimal machine performance."
        )
    else:
        failure_status = "None"
        failure_analysis = (
            f"Based on the provided data, there are no reported failures. The tool wear time is {tool_wear} minutes, which is within the acceptable range."
        )
        root_cause = (
            "No root cause can be identified from the provided data. The tool wear time is the only abnormal value, but it does not indicate a failure."
        )
        risk_level = (
            "Based on the data, the risk level is Low. There are no reported failures, and the tool wear time is within the acceptable range."
        )
        recommendation = (
            "No maintenance is recommended at this time. However, it is recommended to monitor the tool wear time closely and perform regular maintenance ensure optimal machine performance."
        )
        preventive_actions = [
            "Monitor tool wear time closely to prevent excessive wear.",
            "Perform regular maintenance checks to ensure optimal machine performance.",
        ]
        conclusion = (
            "Based on the provided machine data, there is no indication of a failure or risk to the machine. However, it is recommended to monitor the tool wear time closely and perform regular maintenance checks to ensure optimal machine performance."
        )

    preventive_bullets = "\n".join(f"- {action}" for action in preventive_actions)

    return f"""## Maintenance Report for Machine {product_id}

### Machine Health Summary

The current machine health status is as follows:

- Machine Type: {m_type}
- Temperature: Air Temperature: {air_temp:.1f} K, Process Temperature: {proc_temp:.1f} K
- Rotational Speed: {rot_speed} RPM
- Torque: {torque:.1f} Nm
- Tool Wear: {tool_wear} minutes
- Failure Status: {failure_status}

### Failure Analysis

{failure_analysis}

### Root Cause

{root_cause}

### Risk Level

{risk_level}

### Maintenance Recommendation

{recommendation}

### Preventive Actions

{preventive_bullets}

### Final Conclusion

{conclusion}"""



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
