"""HTTP client educato con rate limiting, retry, backoff e header rotation."""

import json
import random
import time
from typing import Any, Optional

import requests

from .config import (
    BACKOFF_403_BASE,
    BACKOFF_BASE,
    DEFAULT_HEADERS,
    MAX_RETRIES,
    MAX_RETRIES_403,
    MAX_TOTAL_WAIT_PER_REQUEST,
    REQUEST_TIMEOUT,
    RETRY_ON_403,
    SLEEP_BETWEEN_REQUESTS,
    USER_AGENTS,
    XHR_HEADERS_EXTRA,
)


class TransfermarktClient:
    """Wrapper su requests.Session con politiche conservative."""

    def __init__(self, sleep: float = SLEEP_BETWEEN_REQUESTS):
        self.session = requests.Session()
        self.sleep = sleep
        self._last_request_time: Optional[float] = None

    def _build_headers(self, *, xhr: bool = False, referer: Optional[str] = None) -> dict:
        h = dict(DEFAULT_HEADERS)
        h["User-Agent"] = random.choice(USER_AGENTS)
        if xhr:
            h.update(XHR_HEADERS_EXTRA)
        if referer:
            h["Referer"] = referer
        return h

    def _wait_if_needed(self) -> None:
        if self._last_request_time is None:
            return
        elapsed = time.monotonic() - self._last_request_time
        wait = self.sleep - elapsed
        if wait > 0:
            time.sleep(wait)

    def _do_get(self, url: str, headers: dict, retries: int) -> requests.Response:
        last_exc: Optional[Exception] = None
        request_started = time.monotonic()
        # Il loop gira fino al massimo tra retries normali e retries-403, perche'
        # il 403 (blocco IP) merita piu' tentativi degli altri errori. I rami
        # interni controllano comunque il proprio limite specifico.
        max_attempts = max(retries, MAX_RETRIES_403 if RETRY_ON_403 else retries)
        for attempt in range(1, max_attempts + 1):
            self._wait_if_needed()
            # Hard-deadline: se cumulativamente abbiamo speso troppo tempo, abort.
            if time.monotonic() - request_started > MAX_TOTAL_WAIT_PER_REQUEST:
                raise RuntimeError(f"GIVE UP {url} after {int(time.monotonic()-request_started)}s")
            try:
                resp = self.session.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
                self._last_request_time = time.monotonic()
                if resp.status_code == 200:
                    return resp
                if resp.status_code in (429, 503):
                    backoff = BACKOFF_BASE * (2 ** (attempt - 1))
                    print(f"    [rate-limited {resp.status_code}] sleep {backoff}s, retry {attempt}/{retries}")
                    time.sleep(backoff)
                    continue
                if resp.status_code == 403 and RETRY_ON_403:
                    # 403 = quasi sempre blocco IP temporaneo (anti-bot). Ritenta con
                    # backoff lungo: l'IP si sblocca dopo minuti, non secondi.
                    # Usa una nuova User-Agent ad ogni tentativo (header rotation gia'
                    # gestita a monte da _build_headers, ma rinnoviamo per sicurezza).
                    if attempt >= MAX_RETRIES_403:
                        print(f"    [403 forbidden] esauriti {MAX_RETRIES_403} tentativi su {url}")
                        resp.raise_for_status()
                    backoff = BACKOFF_403_BASE * (2 ** (attempt - 1))
                    print(f"    [403 forbidden] blocco IP probabile, sleep {backoff}s, retry {attempt}/{MAX_RETRIES_403}")
                    time.sleep(backoff)
                    headers["User-Agent"] = random.choice(USER_AGENTS)
                    continue
                # 404 e altri 4xx: pagina inesistente o errore client, NON ritentare
                resp.raise_for_status()
            except requests.Timeout as e:
                last_exc = e
                print(f"    [timeout] retry {attempt}/{retries} on {url}")
                # niente sleep extra: il timeout l'ha già fatto
            except requests.ConnectionError as e:
                last_exc = e
                backoff = min(BACKOFF_BASE * (2 ** (attempt - 1)), 10)
                print(f"    [connection-error] sleep {backoff}s, retry {attempt}/{retries}")
                time.sleep(backoff)
            except requests.RequestException as e:
                last_exc = e
                backoff = min(BACKOFF_BASE * (2 ** (attempt - 1)), 10)
                print(f"    [{type(e).__name__}] sleep {backoff}s, retry {attempt}/{retries}")
                time.sleep(backoff)
        raise RuntimeError(f"Failed GET {url} after {retries} attempts: {last_exc}")

    def get_html(self, url: str, *, referer: Optional[str] = None, retries: int = MAX_RETRIES) -> str:
        headers = self._build_headers(xhr=False, referer=referer)
        resp = self._do_get(url, headers, retries)
        return resp.text

    def get_json(self, url: str, *, referer: Optional[str] = None, retries: int = MAX_RETRIES) -> Any:
        headers = self._build_headers(xhr=True, referer=referer)
        resp = self._do_get(url, headers, retries)
        try:
            return resp.json()
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Expected JSON but got non-JSON from {url}: {resp.text[:200]!r}") from e
