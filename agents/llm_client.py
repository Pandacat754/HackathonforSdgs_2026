"""Opt-in Chat Completions-compatible transport. No credentials in source."""
import json
import math
import os
import urllib.error
import urllib.parse
import urllib.request


class LLMError(Exception):
    """A sanitised service/configuration failure; never include server bodies."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward an Authorization header to a redirect destination.
        return None


def complete(messages):
    endpoint = os.environ.get("SILENCER_API_URL", "https://api.deepseek.com/chat/completions")
    model = os.environ.get("SILENCER_MODEL", "deepseek-flash")
    api_key = os.environ.get("SILENCER_API_KEY", "")
    parsed = urllib.parse.urlsplit(endpoint)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username
            or parsed.password or parsed.query or parsed.fragment
            or not model.strip() or not api_key.strip()):
        raise LLMError("LLM configuration is missing or invalid")
    try:
        timeout = float(os.environ.get("SILENCER_TIMEOUT_SECONDS", "15"))
        if not math.isfinite(timeout) or not 0 < timeout <= 60:
            raise ValueError()
    except ValueError:
        raise LLMError("Invalid timeout configuration") from None
    payload = {"model": model, "messages": messages,
               "response_format": {"type": "json_object"},
               "max_tokens": 600,
               "thinking": {"type": "disabled"}}
    try:
        request = urllib.request.Request(
            endpoint, data=json.dumps(payload).encode("utf-8"), method="POST",
            headers={"Content-Type": "application/json",
                     "Authorization": "Bearer " + api_key})
        with urllib.request.build_opener(NoRedirect).open(request, timeout=timeout) as response:
            body = response.read(65537)
        if len(body) > 65536:
            raise ValueError("Oversized response")
        envelope = json.loads(body)
        if not isinstance(envelope, dict) or not isinstance(envelope.get("choices"), list):
            raise ValueError("Invalid envelope")
        choice = envelope["choices"][0]
        if not isinstance(choice, dict) or not isinstance(choice.get("message"), dict):
            raise ValueError("Invalid choice")
        if choice.get("finish_reason") != "stop" or choice["message"].get("refusal"):
            raise ValueError("Incomplete or refused response")
        content = choice["message"]["content"]
        if not isinstance(content, str):
            raise ValueError("Invalid content")
        return content
    except (urllib.error.URLError, OSError, ValueError, KeyError, IndexError, TypeError):
        raise LLMError("Model service failed or returned an invalid response") from None
