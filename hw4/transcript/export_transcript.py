"""Preserve actual HW4 Codex session bytes and index recorded messages.

Run from the repository root: python -B hw4/transcript/export_transcript.py
Snapshots are immutable; each invocation creates a new timestamped directory.
"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SOURCES = (
    ("Parts 1-5 and initial audit", Path("D:/CodexCLI/data/sessions/2026/10/16/rollout-2026-10-16T00-16-49-01a142ed-4561-7102-bea4-75f30858c2df.jsonl"),
     "Continue with Part 5: limiting-case tests"),
    ("Completed audit, bug experiment, and export request", Path("D:/CodexCLI/data/sessions/2026/10/16/rollout-2026-10-16T11-43-16-01a14561-bf36-7981-a75b-a2a3390c2f10.jsonl"),
     "Perform the HW4 intentional-bug experiment."),
)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def message_text(payload):
    return "\n".join(part["text"] for part in payload.get("content", [])
                     if isinstance(part, dict) and isinstance(part.get("text"), str))


def main():
    # Validate each complete read before publishing any snapshot. Do not repair,
    # truncate, reserialize, or infer missing records from a compaction summary.
    captures = []
    for label, source, required in SOURCES:
        raw = source.read_bytes()
        records = [(line, json.loads(text)) for line, text in
                   enumerate(raw.decode("utf-8").splitlines(), 1) if text.strip()]
        meta = next(record["payload"] for _, record in records if record["type"] == "session_meta")
        if Path(meta["cwd"]).resolve() != ROOT:
            raise ValueError(f"Unexpected workspace: {source}")
        messages = [(line, record, message_text(record["payload"]))
                    for line, record in records if record["type"] == "response_item"
                    and record["payload"].get("type") == "message"
                    and record["payload"].get("role") in {"user", "assistant"}]
        if not any(required in text for _, record, text in messages
                   if record["payload"]["role"] == "user"):
            raise ValueError(f"Required actual user request missing: {source}")
        captures.append((label, source, raw, records, meta, messages))

    now = datetime.now(timezone.utc)
    folder = OUT / now.strftime("snapshot-%Y%m%dT%H%M%S%fZ")
    folder.mkdir()  # Refuse to overwrite any previous snapshot.
    manifest = {"generated_by": "agent export of actual local Codex JSONL",
                "captured_utc": now.isoformat(), "sessions": [],
                "coverage_limit": "Snapshot of persisted records only; later messages, including the export completion reply, are not included.",
                "excluded_session": {"id": "01a142e8-228e-7ef3-a5c9-56ce3e22444b",
                                     "reason": "Different workspace D:/CodexCLI/vibecoding/HW4; not the HW3_submission testing sessions."}}
    index = ["# HW4 actual Codex transcript index", "",
             "Agent-generated provenance/index; not the user's personal testing log.", "",
             "Two actual local sessions are preserved as byte-identical raw JSONL snapshots.",
             "No messages were reconstructed from reports or conversation summaries.",
             "Raw logs include their original tool records and metadata. The readable",
             "message extraction omits tools/system/developer/reasoning records; use raw",
             "JSONL for the complete stored evidence. Record line numbers are 1-based.", "",
             f"Capture time (UTC): `{now.isoformat()}`.", "",
             f"[Manifest with SHA-256 hashes]({folder.name}/manifest.json).", ""]
    for label, source, raw, records, meta, messages in captures:
        target = folder / source.name
        target.write_bytes(raw)
        if target.read_bytes() != raw:
            raise RuntimeError("Snapshot bytes differ from captured source bytes")
        sid = meta.get("id", meta.get("session_id"))
        readable = folder / f"messages-{sid}.md"
        rendered = [f"# Recorded user/assistant messages: {sid}", "",
                    "Extracted from response_item message records in source order.",
                    "Text below is recorded content, not a newly authored personal log.",
                    "Channel is displayed only if the source stores it. Tool and other",
                    "record types remain available in the raw JSONL.", ""]
        requests = []
        for line, record, text in messages:
            role = record["payload"]["role"]
            channel = record["payload"].get("channel")
            rendered += [f"## Line {line} | {record.get('timestamp')} | {role}" +
                         (f" | {channel}" if channel else ""), ""]
            # A longer fence preserves literal Markdown/code in original text.
            fence = "`" * max(4, max((len(piece) for piece in text.replace("\n", " ").split(" ")
                                      if piece and set(piece) == {"`"}), default=0) + 1)
            while fence in text:
                fence += "`"
            rendered += [fence + "text", text, fence, ""]
            if role == "user" and not text.startswith("<environment_context>"):
                requests.append({"line": line, "timestamp": record.get("timestamp"),
                                 "opening": text.splitlines()[0]})
        readable.write_text("\n".join(rendered), encoding="utf-8")
        entry = {"label": label, "source": str(source), "snapshot": target.name,
                 "sha256": sha256(raw), "bytes": len(raw), "byte_equal_to_captured_source": True,
                 "records": len(records), "session_id": sid, "cwd": meta["cwd"],
                 "first_timestamp": records[0][1].get("timestamp"),
                 "last_timestamp": records[-1][1].get("timestamp"),
                 "harness": {key: meta.get(key) for key in ("originator", "cli_version", "source", "model_provider")},
                 "recorded_models": sorted({record["payload"]["model"] for _, record in records
                                            if record["type"] == "turn_context" and "model" in record["payload"]}),
                 "user_requests": requests, "readable_messages": readable.name,
                 "readable_sha256": sha256(readable.read_bytes())}
        manifest["sessions"].append(entry)
        index += [f"## {label}", "", f"Session `{sid}`.", "",
                  f"[Raw JSONL]({folder.name}/{target.name}) | [Readable recorded messages]({folder.name}/{readable.name})", "",
                  f"{len(records)} records; {len(raw):,} bytes. Recorded interval: "
                  f"`{entry['first_timestamp']}` through `{entry['last_timestamp']}`.", "",
                  "| Actual user request opening | UTC timestamp | Raw line |",
                  "| --- | --- | ---: |"]
        for request in requests:
            opening = request["opening"].replace("|", "\\|")
            index.append(f"| {opening} | {request['timestamp']} | {request['line']} |")
        index += [""]
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    index += ["## Scope and refresh", "",
              "The first session covers Parts 1-5 and the initial 56-test audit work;",
              "the second includes the completed 58-test audit and intentional-bug",
              "experiment, including its completion reply, followed by this export request.",
              "Any compaction records are preserved as recorded, not treated as invented",
              "verbatim copies of earlier messages. The session in the separate HW4",
              "workspace is excluded; its identity and reason are in the manifest.", "",
              "This is a snapshot of persisted records, not a claim that a still-active",
              "conversation is finished. It cannot include the later export completion",
              "reply or future user review. To preserve those after they are logged, run:", "",
              "```powershell", "python -B hw4/transcript/export_transcript.py", "```", "",
              "The script validates the two source sessions, creates another uniquely",
              "named snapshot directory, and updates this index. Earlier snapshots remain",
              "intact. It fails on invalid/incomplete JSON rather than silently dropping",
              "records. This export neither stages/commits files nor edits a personal log.", ""]
    (OUT / "README.md").write_text("\n".join(index), encoding="utf-8")
    print(json.dumps({"snapshot": str(folder), "sessions": [
        {key: entry[key] for key in ("session_id", "bytes", "records", "sha256", "last_timestamp")}
        for entry in manifest["sessions"]]}, indent=2))


if __name__ == "__main__":
    main()
