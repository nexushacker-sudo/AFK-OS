#!/usr/bin/python3
"""Local web interface for Maxence, the AFK OS Ollama assistant."""

from __future__ import annotations

import json
import fcntl
import logging
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


HOST = "127.0.0.1"
PORT = 8765
MODEL = "qwen2.5:1.5b"
OLLAMA = f"http://{HOST}:11434"
APP_DIR = Path(__file__).resolve().parent
PAGE = APP_DIR / "index.html"
LOCAL_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
MAX_BODY = 64 * 1024
MAX_HISTORY = 12
MAX_MESSAGE_CHARS = 4_000
MAX_HISTORY_CHARS = 12_000
SYSTEM_PROMPT = """Tu es Maxence, l'assistant local d'AFK OS. Tu réponds clairement,
avec des étapes utiles et dans la langue employée par la personne (français par
défaut). Tu aides pour AFK OS, Linux/KDE et les questions générales.

Informations fiables sur ce système : AFK OS est une distribution construite à
partir d'Ubuntu 26.04 avec KDE Plasma. La session et les réglages régionaux sont
en français (France), clavier français, fuseau Europe/Paris. Le kit inclut
Firefox, LibreOffice, VLC, Thunderbird, Steam, Discord, Visual Studio Code,
Audacity, GIMP, Inkscape, Krita, Blender, OBS Studio, Kdenlive, Lutris et
Heroic Games Launcher. Des outils KDE, SMB/Samba, Git, Python, Docker,
Wireshark, Wine et Winetricks sont également prévus.

L'IA utilisée est {model}, servie par Ollama sur cet ordinateur. Tu n'as aucun
accès direct aux fichiers, périphériques, réseau, commandes ou état réel de
l'ordinateur. N'affirme jamais avoir exécuté une action ou vérifié le système.
Ne prétends pas connaître les caractéristiques matérielles ou les logiciels
installés actuellement. Si tu n'es pas certain d'un détail propre à AFK OS,
dis-le et propose une façon sûre de le vérifier. Les mises à jour et les
informations du Web ne sont pas accessibles. Reste concis et bienveillant."""

_pull_lock = threading.Lock()
_pull_state: dict[str, object] = {
    "state": "idle",
    "status": "Le modèle sera téléchargé automatiquement au premier lancement.",
    "completed": 0,
    "total": 0,
}


def _ollama_json(path: str, payload: dict[str, object] | None = None,
                 timeout: float = 5) -> dict[str, object]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {} if data is None else {"Content-Type": "application/json"}
    request = urllib.request.Request(f"{OLLAMA}{path}", data=data, headers=headers)
    with LOCAL_OPENER.open(request, timeout=timeout) as response:
        result = json.loads(response.read().decode("utf-8"))
    if not isinstance(result, dict):
        raise ValueError("Réponse Ollama invalide")
    return result


def _model_is_installed() -> bool:
    result = _ollama_json("/api/tags")
    models = result.get("models")
    if not isinstance(models, list):
        raise ValueError("La liste des modèles Ollama est invalide")
    return any(
        isinstance(model, dict)
        and model.get("name") == MODEL
        for model in models
    )


def _pull_model() -> None:
    global _pull_state
    request = urllib.request.Request(
        f"{OLLAMA}/api/pull",
        data=json.dumps({"model": MODEL, "stream": True}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with LOCAL_OPENER.open(request, timeout=3600) as response:
            for raw_line in response:
                if not raw_line.strip():
                    continue
                event = json.loads(raw_line.decode("utf-8"))
                if not isinstance(event, dict):
                    raise ValueError("Réponse de téléchargement Ollama invalide")
                if event.get("error"):
                    raise RuntimeError(str(event["error"]))
                status = str(event.get("status", "Téléchargement du modèle…"))
                completed = event.get("completed", 0)
                total = event.get("total", 0)
                with _pull_lock:
                    _pull_state = {
                        "state": "downloading",
                        "status": status,
                        "completed": completed if isinstance(completed, int) else 0,
                        "total": total if isinstance(total, int) else 0,
                    }
        with _pull_lock:
            _pull_state = {
                "state": "ready",
                "status": "Modèle téléchargé. Maxence est prêt.",
                "completed": 0,
                "total": 0,
            }
    except urllib.error.HTTPError as error:
        detail = error.read(500).decode("utf-8", errors="replace")
        logging.error("Ollama a refusé le téléchargement du modèle: %s", detail)
        with _pull_lock:
            _pull_state = {
                "state": "error",
                "status": "Ollama n'a pas pu télécharger le modèle. Vérifiez la connexion Internet puis réessayez.",
                "completed": 0,
                "total": 0,
            }
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, RuntimeError) as error:
        logging.error("Téléchargement Ollama impossible: %s", error)
        with _pull_lock:
            _pull_state = {
                "state": "error",
                "status": "Le téléchargement du modèle a échoué. Vérifiez Ollama et la connexion Internet puis réessayez.",
                "completed": 0,
                "total": 0,
            }


def _start_model_pull() -> bool:
    with _pull_lock:
        if _pull_state["state"] == "downloading":
            return False
        _pull_state.update(
            state="downloading",
            status="Préparation du téléchargement du modèle…",
            completed=0,
            total=0,
        )
    threading.Thread(target=_pull_model, name="maxence-model-pull", daemon=True).start()
    return True


def _status() -> dict[str, object]:
    try:
        installed = _model_is_installed()
    except urllib.error.HTTPError as error:
        logging.error("Ollama a renvoyé HTTP %s lors de la vérification", error.code)
        return {
            "state": "ollama-offline",
            "status": "Le service Ollama ne répond pas. Réessayez dans quelques instants ou consultez les journaux du système.",
            "model": MODEL,
            "completed": 0,
            "total": 0,
        }
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as error:
        logging.info("Service Ollama indisponible: %s", error)
        return {
            "state": "ollama-offline",
            "status": "Le service Ollama est indisponible. Vérifiez qu'il est démarré puis réessayez.",
            "model": MODEL,
            "completed": 0,
            "total": 0,
        }

    if installed:
        with _pull_lock:
            _pull_state.update(
                state="ready",
                status="Maxence est prêt. L'assistant fonctionne en local.",
                completed=0,
                total=0,
            )
        return {
            "state": "ready",
            "status": "Maxence est prêt. L'assistant fonctionne en local.",
            "model": MODEL,
            "completed": 0,
            "total": 0,
        }

    with _pull_lock:
        state = dict(_pull_state)
    if state["state"] == "idle":
        _start_model_pull()
        with _pull_lock:
            state = dict(_pull_state)
    state["model"] = MODEL
    return state


def _chat(messages: object) -> str:
    if not isinstance(messages, list) or not messages:
        raise ValueError("Écrivez une question pour commencer.")
    if len(messages) > MAX_HISTORY:
        raise ValueError("La conversation est trop longue. Effacez-la puis réessayez.")

    validated: list[dict[str, str]] = []
    total_chars = 0
    for message in messages:
        if not isinstance(message, dict):
            raise ValueError("Format de conversation invalide.")
        role = message.get("role")
        content = message.get("content")
        if role not in ("user", "assistant") or not isinstance(content, str):
            raise ValueError("Format de message invalide.")
        content = content.strip()
        if not content or len(content) > MAX_MESSAGE_CHARS:
            raise ValueError("Chaque message doit contenir au plus 4 000 caractères.")
        total_chars += len(content)
        validated.append({"role": role, "content": content})
    if total_chars > MAX_HISTORY_CHARS:
        raise ValueError("La conversation dépasse la limite autorisée.")

    system = SYSTEM_PROMPT.format(model=MODEL)
    result = _ollama_json(
        "/api/chat",
        {
            "model": MODEL,
            "messages": [{"role": "system", "content": system}, *validated],
            "stream": False,
            "options": {"num_ctx": 4096, "num_predict": 512, "temperature": 0.7},
        },
        timeout=300,
    )
    message = result.get("message")
    if not isinstance(message, dict) or not isinstance(message.get("content"), str):
        raise RuntimeError("Ollama a renvoyé une réponse invalide.")
    answer = message["content"].strip()
    if not answer:
        raise RuntimeError("Ollama a renvoyé une réponse vide.")
    if len(answer) > MAX_MESSAGE_CHARS:
        answer = answer[: MAX_MESSAGE_CHARS - 1].rstrip() + "…"
    return answer


class MaxenceHandler(BaseHTTPRequestHandler):
    server_version = "Maxence"
    sys_version = ""

    def log_message(self, format_string: str, *args: object) -> None:
        logging.info("HTTP %s - %s", self.address_string(), format_string % args)

    def _send_json(self, status: int, data: dict[str, object]) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._security_headers()
        self.end_headers()
        self.wfile.write(body)

    def _security_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; "
            "connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'",
        )

    def _is_local_request(self) -> bool:
        allowed_hosts = {f"{HOST}:{PORT}", f"localhost:{PORT}"}
        if self.headers.get("Host", "").lower() not in allowed_hosts:
            self._send_json(403, {"error": "Accès local uniquement."})
            return False
        origin = self.headers.get("Origin")
        if origin is not None and origin not in (
            f"http://{HOST}:{PORT}",
            f"http://localhost:{PORT}",
        ):
            self._send_json(403, {"error": "Origine de requête refusée."})
            return False
        return True

    def do_GET(self) -> None:
        if not self._is_local_request():
            return
        path = urlsplit(self.path).path
        if path == "/health":
            self._send_json(200, {"service": "afk-maxence"})
        elif path == "/api/status":
            self._send_json(200, _status())
        elif path == "/":
            try:
                page = PAGE.read_bytes()
            except OSError as error:
                logging.error("Interface Maxence illisible: %s", error)
                self._send_json(500, {"error": "L'interface Maxence est introuvable."})
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self._security_headers()
            self.end_headers()
            self.wfile.write(page)
        else:
            self._send_json(404, {"error": "Page introuvable."})

    def do_POST(self) -> None:
        if not self._is_local_request():
            return
        path = urlsplit(self.path).path
        if path == "/api/model/retry":
            status = _status()
            if status["state"] == "ollama-offline":
                self._send_json(503, status)
                return
            if status["state"] == "ready":
                self._send_json(200, status)
                return
            _start_model_pull()
            self._send_json(202, _status())
            return
        if path != "/api/chat":
            self._send_json(404, {"error": "Page introuvable."})
            return

        content_length = self.headers.get("Content-Length")
        if content_length is None or not content_length.isdecimal():
            self._send_json(411, {"error": "Longueur de requête invalide."})
            return
        length = int(content_length)
        if length > MAX_BODY:
            self._send_json(413, {"error": "La requête est trop volumineuse."})
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(400, {"error": "La requête n'est pas un JSON valide."})
            return
        if not isinstance(payload, dict):
            self._send_json(400, {"error": "Format de requête invalide."})
            return
        try:
            answer = _chat(payload.get("messages"))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            logging.error("Réponse Ollama illisible: %s", error)
            self._send_json(502, {"error": "Ollama a renvoyé une réponse illisible."})
            return
        except ValueError as error:
            self._send_json(400, {"error": str(error)})
            return
        except RuntimeError as error:
            logging.error("Réponse Ollama invalide: %s", error)
            self._send_json(502, {"error": "Ollama a renvoyé une réponse invalide."})
            return
        except urllib.error.HTTPError as error:
            detail = error.read(500).decode("utf-8", errors="replace")
            logging.error("Erreur Ollama HTTP %s: %s", error.code, detail)
            self._send_json(
                502,
                {"error": "Ollama n'a pas pu répondre. Vérifiez que le modèle est prêt."},
            )
            return
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            logging.error("Ollama est inaccessible pendant la réponse: %s", error)
            self._send_json(
                503,
                {"error": "Ollama est indisponible. Vérifiez son service puis réessayez."},
            )
            return
        self._send_json(200, {"answer": answer})


def _is_running() -> bool:
    try:
        request = urllib.request.Request(f"http://{HOST}:{PORT}/health")
        with LOCAL_OPENER.open(request, timeout=0.5) as response:
            return json.loads(response.read().decode("utf-8")) == {
                "service": "afk-maxence"
            }
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return False


def _launcher_paths() -> tuple[Path, Path]:
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    state_dir = Path(runtime) / "afk-maxence" if runtime else (
        Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
        / "afk-maxence"
    )
    if state_dir.is_symlink():
        raise OSError("Le dossier temporaire de Maxence ne doit pas être un lien.")
    state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    state_dir.chmod(0o700)
    profile_dir = (
        Path.home()
        / ".var"
        / "app"
        / "org.mozilla.firefox"
        / "afk-maxence-profile"
    )
    if profile_dir.is_symlink():
        raise OSError("Le profil privé de Firefox ne doit pas être un lien.")
    profile_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    profile_dir.chmod(0o700)
    return state_dir / "firefox.pid", profile_dir


def _owned_firefox(pid: int, profile_dir: Path) -> bool:
    try:
        if os.getpgid(pid) != pid:
            return False
        process_stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
        process_state = process_stat.rsplit(")", 1)[1].split()[0]
        if process_state == "Z":
            return False
        arguments = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
    except (OSError, IndexError):
        return False
    required = (
        b"org.mozilla.firefox",
        b"--no-remote",
        b"--new-window",
        os.fsencode(str(profile_dir)),
    )
    return all(argument in arguments for argument in required)


def _start_server() -> bool:
    if not _is_running():
        log_dir = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
        log_dir = log_dir / "afk-maxence"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = (log_dir / "server.log").open("a", encoding="utf-8")
        try:
            subprocess.Popen(
                [sys.executable, str(Path(__file__).resolve()), "--serve"],
                stdin=subprocess.DEVNULL,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                close_fds=True,
            )
        finally:
            log_file.close()

    for _ in range(40):
        if _is_running():
            return True
        time.sleep(0.25)
    return False


def _toggle_app() -> int:
    try:
        pid_path, profile_dir = _launcher_paths()
        lock_path = pid_path.with_suffix(".lock")
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
            try:
                pid = int(pid_path.read_text(encoding="ascii").strip())
            except (FileNotFoundError, ValueError):
                pid = 0

            if pid and _owned_firefox(pid, profile_dir):
                os.killpg(pid, signal.SIGTERM)
                for _ in range(40):
                    if not _owned_firefox(pid, profile_dir):
                        break
                    time.sleep(0.1)
                if _owned_firefox(pid, profile_dir):
                    raise OSError("Firefox ne s'est pas fermé ; Maxence reste ouvert.")
                pid_path.unlink(missing_ok=True)
                return 0
            pid_path.unlink(missing_ok=True)

            if not _start_server():
                raise OSError(
                    "Le serveur local n'a pas démarré. Consultez "
                    "~/.cache/afk-maxence/server.log."
                )
            flatpak = shutil.which("flatpak")
            if flatpak is None:
                raise OSError("Firefox Flatpak est introuvable.")

            command = [
                flatpak,
                "run",
                "--branch=stable",
                "org.mozilla.firefox",
                "--no-remote",
                "--profile",
                str(profile_dir),
                "--new-window",
                f"http://{HOST}:{PORT}/",
            ]
            log_dir = Path(
                os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")
            ) / "afk-maxence"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir / "server.log"
            with log_path.open("a", encoding="utf-8") as log_file:
                process = subprocess.Popen(
                    command,
                    stdin=subprocess.DEVNULL,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                    close_fds=True,
                )
            time.sleep(0.5)
            if process.poll() is not None:
                raise OSError(
                    "La fenêtre Firefox de Maxence n'a pas pu s'ouvrir. "
                    "Consultez ~/.cache/afk-maxence/server.log."
                )
            pid_path.write_text(f"{process.pid}\n", encoding="ascii")
            return 0
        finally:
            os.close(lock_fd)
    except OSError as error:
        logging.error("Impossible de basculer Maxence: %s", error)
        print(f"Maxence : {error}", file=sys.stderr)
        return 1


def main() -> int:
    if "--toggle" in sys.argv:
        return _toggle_app()
    if "--serve" not in sys.argv:
        print(f"Usage: {Path(sys.argv[0]).name} --open|--serve", file=sys.stderr)
        return 2
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    server = ThreadingHTTPServer((HOST, PORT), MaxenceHandler)
    server.daemon_threads = True
    logging.info("Maxence écoute uniquement sur http://%s:%s", HOST, PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("Arrêt demandé")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
