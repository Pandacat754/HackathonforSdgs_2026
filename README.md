# Silencer

## Overview

Silencer is an AI-powered assistant that helps employees disconnect from work during evenings, weekends, and holidays without worrying about missing important messages.

The system analyzes incoming work messages, assesses urgency, drafts appropriate acknowledgements, and queues non-urgent messages for review the next morning.

## Problem Statement

Many employees feel compelled to check work messages outside working hours because they fear missing important updates, deadlines, or decisions.

Silencer aims to:

- Reduce after-hours interruptions
- Identify genuinely urgent messages
- Draft appropriate replies
- Queue non-urgent messages for later review
- Improve work-life balance

## Demo Workflow

1. The app analyzes all sample messages on first load and keeps the results in the current Streamlit session.
2. Non-Urgent messages appear in the morning review queue automatically.
3. The highest-priority urgent message is highlighted above the inbox; all messages also appear in the message list.
4. For Needs Human Review messages, choosing "Yes, review in morning" changes the category to Non-Urgent and moves the message into the morning queue. Choosing "No, handle tonight" changes it to Urgent and makes it eligible for the highest-priority panel.

The highest-priority panel shows the Urgent message with the earliest valid `received_at` timestamp. Messages without a valid timestamp are considered after timestamped messages; ties retain the original message order. The app can re-analyze an individual message.

Message cards show the message ID, category, urgency, sender, received time, message, suggested reply, and app name. The urgency level uses the same numeric, color-coded pill in message cards, the priority panel, and the popup. The same message keeps one read/unread state across the priority card, inbox, and morning queue, keyed by message ID. Unread cards use a blue left border. On a Needs Human Review card, **Manual reply** marks the message as replied and moves it to History. Other reply actions also resolve messages into History.

The Analyzed counter shows messages not classified as Needs Human Review over the active message total. Resolving a certain message decreases both values; resolving an uncertain message decreases only the total.

## Project Structure

```text
HackathonforSdgs_2026/

├── app.py
├── README.md
├── requirements.txt
├── .gitignore
│
├── data/
│   └── sample_messages.json
│
├── agents/
│   ├── classifier.py
│   ├── reply_generator.py
│   └── prompts.py
│
└── queue/
    └── morning_queue.py
```

## Shared Message Format

```json
{
  "id": "msg001",
  "sender": "Project Manager",
  "app": "Teams",
  "message": "Can you send me the final report tonight?"
}
```

`app` identifies the source platform and must be one of `Teams`, `Gmail`,
`Outlook`, or `Whatsapp`. Message cards and detail popups display it as `From:`.

## AI Classification Interface

### classify_message()

Location:

```python
agents/classifier.py
```

Expected Output:

```python
{
    "category": "urgent",
    "classification": "Urgent",
    "urgency_score": 0.95,
    "reason": "The message describes a current operational or safety incident.",
    "source": "mock",
    "requires_user_confirmation": True
}
```

## Reply Generation Interface

### generate_reply()

Location:

```python
agents/reply_generator.py
```

Expected Output:

```python
{
    "suggested_reply": "...",
    "is_draft": True,
    "requires_user_confirmation": True
}
```

### Relationship & Tone Map

Open **Settings** and toggle **Show Relationship & Tone Map** to show or hide
the mind map and profile input form. Choose an existing contact to update or
select **Add contact**, then enter a name, relationship type, and preferred
tone. Saving immediately refreshes the mind map and any affected draft replies.
Choose an existing contact and select **Delete contact** to remove it from the
map; deleted contacts are not added again automatically.
Relationship categories are parent nodes; contact nodes show the selected tone,
with a tooltip explaining the tone choice. The form supports Family, Friend,
Lecturer, Classmate, Teammate, Client, Manager, Colleague, and Other
relationships, and Casual, Friendly, Professional, Formal, Respectful,
Empathetic, and Direct tones.

New contacts receive a preliminary relationship and tone suggestion based on
the sender label and available message history. Review and adjust these
suggestions in Settings. Lecturer, Friend, and Client profiles default to
respectful/professional, casual/friendly, and formal/professional wording,
respectively. Relationship and tone preferences are provided to the agent as
personalization context; they never affect urgency or authorize commitments.
Saved profiles and deleted-contact exclusions are stored locally in
`data/relationship_map.json`. Existing saved relationship-map profiles are
migrated when loaded.

Use **Message category labels** to show standard category names or priority
codes. Priority-code mode defaults to P0 for urgent, P2 for not urgent, and -1
for messages needing manual review; the urgent and not-urgent codes can be
changed in Settings. These labels only affect display, not triage decisions.
Display preferences are stored locally in `data/category_display.json`.
Priority mode always displays human-review messages as **P-1**. Thumbs-up or
thumbs-down reply ratings are stored locally in `data/reply_feedback.json` and
adjust the preferred response style for that sender. Use the computer/phone
icon in the heading to switch between desktop and compact mobile layouts.

## Queue Interface

Location:

```python
morning_queue.py
```

Functions:

```python
get_queue(messages, analyses, review_decisions)
```

Purpose:

The morning review queue automatically includes analyzed Non-Urgent messages. Choosing morning review converts a Needs Human Review message into Non-Urgent and adds it to the queue. In the queue, choosing "Not urgent" marks the message Confirmed and replaces the choice buttons with a checkmark. Choosing "Urgent and send reply now" changes it to Urgent and removes it from the queue. Clicking a send-reply action resolves the message, moves it from active lists into History, and decreases the active message count. For messages requiring human handling, **Manual reply** marks the message as replied, moves it into History, and decreases the active count.

History uses the same message-card layout and is captioned "Review past messages here." It records messages resolved through a send-reply or Manual reply action.


## Running the Project

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the application:

```bash
python -m streamlit run app.py
```

## Vision

Silencer acts as a trusted AI intermediary during non-working hours.

Instead of forcing users to constantly monitor work chats, Silencer filters messages, highlights genuinely urgent issues, drafts appropriate acknowledgements, and presents deferred messages in a morning review dashboard.
