"""Flask web application for Teams Meeting Summarizer."""

import traceback

from flask import (
    Flask,
    redirect,
    render_template,
    request,
    session,
    url_for,
    flash,
    send_file,
)

from app.auth import (
    acquire_token_by_code,
    get_auth_url,
    is_authenticated,
    logout,
    get_access_token,
)
from app.config import Config
from app.graph_client import GraphClient
from app.summarizer import summarize_meeting, summarize_raw_text
from app.exporter import export_markdown, export_pdf, export_text


def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.secret_key = Config.SECRET_KEY

    # ── Routes ─────────────────────────────────────────────────

    @app.route("/")
    def index():
        authenticated = is_authenticated()
        return render_template("index.html", authenticated=authenticated)

    @app.route("/login")
    def login():
        auth_url = get_auth_url()
        return redirect(auth_url)

    @app.route("/callback")
    def callback():
        code = request.args.get("code")
        if not code:
            flash("Authentication failed: no code received.", "error")
            return redirect(url_for("index"))

        result = acquire_token_by_code(code)
        if "error" in result:
            flash(f"Authentication error: {result.get('error_description', result['error'])}", "error")
            return redirect(url_for("index"))

        flash("Successfully signed in!", "success")
        return redirect(url_for("meetings"))

    @app.route("/logout")
    def logout_route():
        logout()
        flash("Signed out successfully.", "success")
        return redirect(url_for("index"))

    @app.route("/meetings")
    def meetings():
        if not is_authenticated():
            return redirect(url_for("login"))

        try:
            client = GraphClient()
            user = client.get_me()
            events = client.get_recent_events()
            return render_template(
                "meetings.html",
                user=user,
                events=events,
                authenticated=True,
            )
        except Exception as e:
            flash(f"Error fetching meetings: {e}", "error")
            return render_template("meetings.html", user=None, events=[], authenticated=True)

    @app.route("/summarize/<event_index>")
    def summarize(event_index):
        if not is_authenticated():
            return redirect(url_for("login"))

        try:
            client = GraphClient()
            events = client.get_recent_events()
            idx = int(event_index)
            if idx >= len(events):
                flash("Meeting not found.", "error")
                return redirect(url_for("meetings"))

            event = events[idx]
            meeting_data = client.fetch_meeting_data(event)
            summary = summarize_meeting(meeting_data)

            return render_template(
                "summary.html",
                meeting=meeting_data,
                summary=summary,
                event_index=idx,
                authenticated=True,
            )
        except Exception as e:
            flash(f"Error summarizing meeting: {e}", "error")
            traceback.print_exc()
            return redirect(url_for("meetings"))

    @app.route("/summarize-text", methods=["GET", "POST"])
    def summarize_text():
        if request.method == "POST":
            text = request.form.get("transcript_text", "").strip()
            if not text:
                flash("Please paste some meeting content to summarize.", "error")
                return render_template("paste.html", authenticated=is_authenticated())

            try:
                summary = summarize_raw_text(text)
                return render_template(
                    "summary.html",
                    meeting={"subject": "Pasted Transcript", "start": "", "end": ""},
                    summary=summary,
                    event_index=None,
                    authenticated=is_authenticated(),
                )
            except Exception as e:
                flash(f"Error summarizing: {e}", "error")
                return render_template("paste.html", authenticated=is_authenticated())

        return render_template("paste.html", authenticated=is_authenticated())

    @app.route("/export/<fmt>", methods=["POST"])
    def export(fmt):
        summary = request.form.get("summary", "")
        subject = request.form.get("subject", "meeting")

        if not summary:
            flash("No summary to export.", "error")
            return redirect(url_for("meetings"))

        try:
            if fmt == "pdf":
                filepath = export_pdf(summary, subject)
            elif fmt == "markdown":
                filepath = export_markdown(summary, subject)
            elif fmt == "text":
                filepath = export_text(summary, subject)
            else:
                flash("Unsupported format.", "error")
                return redirect(url_for("meetings"))

            return send_file(filepath, as_attachment=True)
        except Exception as e:
            flash(f"Export error: {e}", "error")
            return redirect(url_for("meetings"))

    return app
