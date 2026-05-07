"""
Integracion con Gmail API (OAuth) para leer bandeja y enviar correos.
"""

from __future__ import annotations

import base64
import os
from email.mime.text import MIMEText
from pathlib import Path


SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

_ROOT = Path(__file__).resolve().parent.parent
_TOKEN_PATH = _ROOT / "gmail_token.json"


def _credentials_path() -> Path | None:
    env_path = os.environ.get("GMAIL_CREDENTIALS_PATH")
    if env_path:
        p = Path(env_path).expanduser()
        if p.exists():
            return p

    for name in (
        "gmail_credentials.json",
        "gmail_crediantials.json",
        "credentials.json",
    ):
        p = _ROOT / name
        if p.exists():
            return p
    return None


def _build_service():
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        return None, (
            "Falta integrar Gmail. Instala dependencias con: "
            "pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
        )

    creds = None

    if _TOKEN_PATH.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(_TOKEN_PATH), SCOPES)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            cred_path = _credentials_path()
            if not cred_path:
                return None, (
                    "No encontre credenciales de Gmail. Coloca 'gmail_credentials.json' "
                    "(o 'credentials.json') en la raiz del proyecto para autorizar."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(cred_path), SCOPES)
            creds = flow.run_local_server(port=0)

        _TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")

    service = build("gmail", "v1", credentials=creds)
    return service, None


def _header(headers: list[dict], name: str) -> str:
    name_lower = name.lower()
    for h in headers:
        if str(h.get("name", "")).lower() == name_lower:
            return str(h.get("value", "")).strip()
    return ""


def read_inbox(max_results: int = 5) -> str:
    service, error = _build_service()
    if error:
        return error

    max_results = max(1, min(10, int(max_results)))

    try:
        result = service.users().messages().list(
            userId="me",
            labelIds=["INBOX"],
            maxResults=max_results,
        ).execute()
        items = result.get("messages", [])

        if not items:
            return "Revise tu bandeja de entrada: no tienes correos recientes."

        previews = []
        for msg in items[:3]:
            data = service.users().messages().get(
                userId="me",
                id=msg.get("id"),
                format="metadata",
                metadataHeaders=["From", "Subject"],
            ).execute()
            headers = data.get("payload", {}).get("headers", [])
            from_value = _header(headers, "From") or "Remitente desconocido"
            subject_value = _header(headers, "Subject") or "Sin asunto"
            previews.append(f"De {from_value}, asunto: {subject_value}")

        base = f"Revise tu bandeja. Encontre {len(items)} correos recientes."
        detail = " ".join(previews)
        return f"{base} {detail}".strip()
    except Exception as exc:
        return f"No pude revisar Gmail en este momento. Error: {exc}"


def send_email(to_email: str, subject: str, body: str) -> str:
    service, error = _build_service()
    if error:
        return error

    to_email = to_email.strip()
    subject = subject.strip()
    body = body.strip()

    if not to_email or "@" not in to_email:
        return "No pude enviar el correo: destinatario invalido."

    if not subject:
        subject = "Sin asunto"

    try:
        message = MIMEText(body or "")
        message["to"] = to_email
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()
        msg_id = sent.get("id", "")
        if msg_id:
            return f"Correo enviado correctamente a {to_email}."
        return "Correo enviado correctamente."
    except Exception as exc:
        return f"No pude enviar el correo. Error: {exc}"
