"""Microsoft Graph API client for fetching Teams meeting data."""

import requests

from app.auth import get_access_token
from app.config import Config


class GraphClient:
    """Client to interact with Microsoft Graph API for Teams meetings."""

    def __init__(self):
        self.base_url = Config.GRAPH_API_BASE

    def _headers(self):
        token = get_access_token()
        if not token:
            raise RuntimeError("Not authenticated. Please sign in first.")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _get(self, endpoint, params=None):
        url = f"{self.base_url}{endpoint}"
        resp = requests.get(url, headers=self._headers(), params=params)
        resp.raise_for_status()
        return resp.json()

    # ── User info ──────────────────────────────────────────────

    def get_me(self):
        """Get the signed-in user's profile."""
        return self._get("/me")

    # ── Online meetings ────────────────────────────────────────

    def get_recent_events(self, top=20):
        """Get recent calendar events that are Teams meetings."""
        data = self._get("/me/events", params={
            "$top": top,
            "$orderby": "start/dateTime desc",
            "$filter": "isOnlineMeeting eq true",
            "$select": "id,subject,start,end,onlineMeeting,organizer,attendees",
        })
        return data.get("value", [])

    def get_online_meeting(self, join_url):
        """Get online meeting details by join URL."""
        # Extract meeting ID from join URL via filter
        data = self._get("/me/onlineMeetings", params={
            "$filter": f"JoinWebUrl eq '{join_url}'",
        })
        meetings = data.get("value", [])
        return meetings[0] if meetings else None

    # ── Transcripts ────────────────────────────────────────────

    def get_meeting_transcripts(self, meeting_id):
        """List transcripts available for a meeting."""
        data = self._get(f"/me/onlineMeetings/{meeting_id}/transcripts")
        return data.get("value", [])

    def get_transcript_content(self, meeting_id, transcript_id):
        """Download the actual transcript text content."""
        url = (
            f"{self.base_url}/me/onlineMeetings/{meeting_id}"
            f"/transcripts/{transcript_id}/content"
        )
        token = get_access_token()
        resp = requests.get(url, headers={
            "Authorization": f"Bearer {token}",
            "Accept": "text/vtt",
        })
        resp.raise_for_status()
        return resp.text

    # ── Chat messages (meeting chat) ───────────────────────────

    def get_meeting_chat(self, chat_id, top=50):
        """Get chat messages from a meeting chat thread."""
        data = self._get(f"/chats/{chat_id}/messages", params={
            "$top": top,
            "$orderby": "createdDateTime desc",
        })
        return data.get("value", [])

    # ── Call records (for metadata) ────────────────────────────

    def get_recent_call_records(self, top=10):
        """Get recent call records."""
        data = self._get("/communications/callRecords", params={
            "$top": top,
            "$orderby": "startDateTime desc",
        })
        return data.get("value", [])

    # ── Convenience: fetch all meeting data ────────────────────

    def fetch_meeting_data(self, event):
        """
        Given a calendar event dict, fetch all available data:
        transcript text, chat messages, and metadata.
        Returns a consolidated dict.
        """
        result = {
            "subject": event.get("subject", "Untitled Meeting"),
            "start": event.get("start", {}).get("dateTime", ""),
            "end": event.get("end", {}).get("dateTime", ""),
            "organizer": event.get("organizer", {}).get(
                "emailAddress", {}
            ).get("name", "Unknown"),
            "attendees": [
                a.get("emailAddress", {}).get("name", "")
                for a in event.get("attendees", [])
            ],
            "transcript": None,
            "chat_messages": [],
        }

        # Try to get the online meeting details and transcript
        online_meeting = event.get("onlineMeeting", {})
        join_url = online_meeting.get("joinUrl", "")

        if join_url:
            meeting = self.get_online_meeting(join_url)
            if meeting:
                meeting_id = meeting["id"]
                # Fetch transcripts
                transcripts = self.get_meeting_transcripts(meeting_id)
                if transcripts:
                    transcript_text = self.get_transcript_content(
                        meeting_id, transcripts[0]["id"]
                    )
                    result["transcript"] = transcript_text

                # Fetch chat messages if chat thread exists
                chat_id = meeting.get("chatInfo", {}).get("threadId")
                if chat_id:
                    messages = self.get_meeting_chat(chat_id)
                    result["chat_messages"] = [
                        {
                            "sender": m.get("from", {}).get(
                                "user", {}
                            ).get("displayName", "Unknown"),
                            "content": m.get("body", {}).get("content", ""),
                            "time": m.get("createdDateTime", ""),
                        }
                        for m in messages
                    ]

        return result
