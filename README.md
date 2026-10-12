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

```
Incoming Work Message
         ↓
 AI Urgency Assessment
         ↓
      Urgent?
      /     \
    Yes      No
     ↓        ↓
 Notify     Generate
  User      Reply
              ↓
        Add to Queue
              ↓
      Morning Review
```

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
  "message": "Can you send me the final report tonight?"
}
```

## AI Classification Interface

### classify_message()

Location:

```python
agents/classifier.py
```

Expected Output:

```python
{
    "classification": "Urgent",
    "urgency_score": 0.95,
    "reason": "Contains immediate deadline"
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
    "suggested_reply":
    "Thank you for your message. I will review it tomorrow morning."
}
```

## Queue Interface

Location:

```python
queue/morning_queue.py
```

Functions:

```python
add_to_queue(message)

get_queue()
```

Purpose:

- Store non-urgent messages
- Display deferred messages the next morning
- Support morning review workflow

## Team Roles

### Person A – Framework & Integration

Responsibilities:

- Streamlit UI
- GitHub repository management
- System integration
- Final demo preparation

### Person B – AI Agent

Responsibilities:

- Message classification
- Urgency assessment
- Reply generation
- Prompt engineering

### Person C – Queue & Testing

Responsibilities:

- Morning queue development
- Test data preparation
- Workflow testing
- Demo support

## Current Progress

### Completed

- GitHub repository created
- Streamlit setup completed
- Initial project structure created
- Shared message format defined

### In Progress

- AI classification module
- Reply generation module
- Queue system implementation
- UI improvements

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
