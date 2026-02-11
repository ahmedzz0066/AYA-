"""AI-powered meeting summarization using OpenAI."""

from openai import OpenAI

from app.config import Config

SYSTEM_PROMPT = """You are an expert meeting summarizer. Analyze the provided
meeting transcript and/or chat messages and produce a clear, structured summary.

Your summary MUST include these sections:

## Meeting Overview
- Meeting title, date, duration, participants

## Key Discussion Points
- Bullet points of the main topics discussed

## Decisions Made
- Any decisions that were agreed upon during the meeting

## Action Items
- Specific tasks assigned, with the responsible person if mentioned
- Format: [ ] Task description — @Person (if known)

## Important Notes
- Any deadlines, risks, blockers, or notable information mentioned

Keep the summary concise but comprehensive. Use clear language.
If information is missing or unclear, note it rather than guessing."""


def summarize_meeting(meeting_data):
    """
    Summarize meeting data using OpenAI.

    Args:
        meeting_data: dict with keys: subject, start, end, organizer,
                      attendees, transcript, chat_messages

    Returns:
        str: The AI-generated summary in markdown format.
    """
    # Build the content to summarize
    parts = []

    parts.append(f"Meeting: {meeting_data.get('subject', 'Untitled')}")
    parts.append(f"Date: {meeting_data.get('start', 'Unknown')}")
    parts.append(f"End: {meeting_data.get('end', 'Unknown')}")
    parts.append(f"Organizer: {meeting_data.get('organizer', 'Unknown')}")

    attendees = meeting_data.get("attendees", [])
    if attendees:
        parts.append(f"Attendees: {', '.join(attendees)}")

    # Add transcript
    transcript = meeting_data.get("transcript")
    if transcript:
        parts.append("\n--- TRANSCRIPT ---")
        parts.append(transcript)

    # Add chat messages
    chat_messages = meeting_data.get("chat_messages", [])
    if chat_messages:
        parts.append("\n--- CHAT MESSAGES ---")
        for msg in chat_messages:
            sender = msg.get("sender", "Unknown")
            content = msg.get("content", "")
            time = msg.get("time", "")
            parts.append(f"[{time}] {sender}: {content}")

    if not transcript and not chat_messages:
        parts.append(
            "\nNo transcript or chat messages available for this meeting. "
            "Summarize based on the metadata above."
        )

    content = "\n".join(parts)

    client = OpenAI(api_key=Config.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=Config.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
        temperature=0.3,
        max_tokens=2000,
    )

    return response.choices[0].message.content


def summarize_raw_text(text):
    """
    Summarize raw text (e.g., a pasted transcript).

    Args:
        text: Raw meeting transcript or notes.

    Returns:
        str: The AI-generated summary in markdown format.
    """
    client = OpenAI(api_key=Config.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=Config.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Please summarize the following meeting content:\n\n{text}",
            },
        ],
        temperature=0.3,
        max_tokens=2000,
    )

    return response.choices[0].message.content
