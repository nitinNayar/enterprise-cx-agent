# Arize Session Tracking Implementation

## Overview

This document describes the implementation of **session tracking** in Arize Phoenix for the Enterprise CX Agent. Session tracking groups related traces by `session.id`, enabling full conversation analysis in the Arize UI.

## What Was Implemented

### 1. OpenInference Session Context Integration

**Files Modified:**
- `agent/agent.py` - Added session context wrapper around Anthropic API calls
- `app.py` - Added user tracking from Chainlit sessions

**Key Changes:**

#### agent/agent.py
```python
from openinference.instrumentation import using_attributes

# Wrap Anthropic calls with session context
with using_attributes(
    session_id=self.session_id,
    user_id=user_id,  # Optional: for cross-session user tracking
    metadata={
        "category": category.value if category else "default",
        "num_tools": len(filtered_tools),
        "conversation_turn": len([m for m in self.messages if m["role"] == "user"]),
        "model": Config.MODEL_NAME
    }
):
    response = self.client.messages.create(...)
```

#### app.py
```python
# Capture Chainlit user for cross-session tracking
user = cl.user_session.get("user")
if user:
    user_id = getattr(user, 'identifier', None) or getattr(user, 'id', None)
    cl.user_session.set("user_id", user_id)

# Pass user_id to agent
response = agent.run(message.content, category=category, user_id=user_id)
```

## How It Works

### Session Tracking Flow

1. **Session ID Generation** (agent/agent.py:45-46)
   - When a new conversation starts, a unique session ID is generated: `SESSION-{uuid}`
   - This ID persists throughout the entire conversation

2. **OpenInference Context Attachment** (agent/agent.py:90-110)
   - Every Anthropic API call is wrapped with `using_attributes()` context manager
   - The session ID is automatically attached to all spans/traces
   - Additional metadata is included for better observability

3. **Arize Ingestion**
   - OpenTelemetry spans include the `session.id` attribute
   - Arize Phoenix automatically groups traces by session ID
   - Traces appear in the "Sessions" tab in Arize UI

### Metadata Tracked

For each LLM call, the following attributes are tracked:

| Attribute | Description | Example |
|-----------|-------------|---------|
| `session.id` | Unique conversation identifier | `SESSION-a7b3c4d1` |
| `user.id` | User identifier (if authenticated) | `user@example.com` |
| `metadata.category` | Question routing category | `ORDER_STATUS`, `RETURNS_REFUNDS`, `GENERAL` |
| `metadata.num_tools` | Number of tools available | `8` |
| `metadata.conversation_turn` | Turn number in conversation | `3` |
| `metadata.model` | Model being used | `claude-sonnet-4-20250514` |

## Viewing Sessions in Arize UI

### Accessing the Sessions Tab

1. **Navigate to your project** in Arize AX:
   - URL: `https://app.arize.com/organizations/{org_id}/spaces/{space_id}/projects/{project_id}`

2. **Click the "Sessions" tab** in the navigation bar (next to Traces, Spans, Agent Graph, Agent Path)

3. **View session list:**
   - Each row represents a complete conversation (grouped by session.id)
   - Click on a session to see all traces in that conversation
   - Analyze the full user-AI interaction flow

### Key Features Now Available

✅ **Session Grouping**: All traces from a single conversation are grouped together

✅ **Multi-Turn Analysis**: See the complete conversation flow across multiple messages

✅ **Session-Level Metrics**: Identify performance issues across entire conversations

✅ **Conversation Breakdown Detection**: Find where conversations "break" or go off rails

✅ **User Tracking**: Track the same user across multiple sessions (if authenticated)

## Verification Steps

### 1. Start the Application

```bash
chainlit run app.py
```

### 2. Have a Multi-Turn Conversation

Example conversation:
```
User: "I want to return my order ORD-12345"
Agent: "Let me look up your order... Can you tell me the reason?"
User: "The book arrived damaged"
Agent: "I've processed your refund..."
```

### 3. Check Arize UI

1. Go to: https://app.arize.com (Phoenix Cloud)
2. Navigate to your project: `enterprise-cx-agent`
3. Click the **"Sessions"** tab
4. Look for your session ID (format: `SESSION-xxxxxxxx`)
5. Click on the session to view all traces grouped together

### 4. Verify Session Attributes

In the Arize UI, you should see:
- **session.id**: Your conversation's session ID
- **user.id**: User identifier (if authenticated)
- **Metadata**: Category, conversation turn, model info
- **Grouped Traces**: All LLM calls from the conversation linked together

## Best Practices

### 1. Session ID Persistence
- ✅ Session IDs persist throughout the entire conversation
- ✅ New session IDs are generated for new conversations
- ❌ Don't reuse session IDs across different users

### 2. User Tracking
- ✅ Use user.id for tracking the same user across multiple sessions
- ✅ Capture authenticated user identifiers when available
- ❌ Don't use PII (personally identifiable information) as user IDs

### 3. Metadata
- ✅ Add contextual metadata that helps debugging (category, turn number)
- ✅ Keep metadata concise and relevant
- ❌ Don't include sensitive data in metadata

### 4. Session-Level Evaluations
- ✅ Run evaluations at the session level for conversation quality
- ✅ Track metrics like "conversation completion rate"
- ✅ Identify sessions where users drop off or escalate

## Technical Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────┐
│                   app.py                        │
│  ┌──────────────────────────────────────────┐  │
│  │  Chainlit User Session                   │  │
│  │  - Captures user.identifier              │  │
│  │  - Stores user_id in session             │  │
│  └──────────────────────────────────────────┘  │
│                      ↓                          │
│              agent.run(user_id)                 │
└─────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│                agent/agent.py                   │
│  ┌──────────────────────────────────────────┐  │
│  │  using_attributes(                       │  │
│  │    session_id=self.session_id,           │  │
│  │    user_id=user_id,                      │  │
│  │    metadata={...}                        │  │
│  │  )                                        │  │
│  └──────────────────────────────────────────┘  │
│                      ↓                          │
│          client.messages.create()               │
└─────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│         AnthropicInstrumentor                   │
│  (openinference-instrumentation-anthropic)      │
│  - Auto-instruments Anthropic API calls         │
│  - Attaches session.id to spans                 │
│  - Exports to OpenTelemetry                     │
└─────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│         OpenTelemetry Exporter                  │
│  (arize-otel)                                   │
│  - Batches spans                                │
│  - Sends to Phoenix Cloud                       │
└─────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│            Arize Phoenix Cloud                  │
│  - Receives spans with session.id               │
│  - Groups traces by session                     │
│  - Displays in Sessions UI tab                  │
└─────────────────────────────────────────────────┘
```

## Troubleshooting

### Sessions Not Appearing in Arize UI

**Problem**: No sessions visible in the Sessions tab

**Solutions**:
1. **Check session ID format**: Must be a non-empty string
   ```python
   # Verify in logs
   logger.info(f"Session ID: {self.session_id}")
   ```

2. **Verify context manager is active**: Ensure `using_attributes()` wraps the API call
   ```python
   # Check that the with statement is present
   with using_attributes(session_id=...):
       response = self.client.messages.create(...)
   ```

3. **Check Phoenix connection**: Verify tracing is working
   ```bash
   # Look for startup message
   🔭 Observability: Tracing enabled. Sending to Phoenix Cloud
   ```

4. **Validate environment variables**: Ensure Phoenix Cloud credentials are set
   ```bash
   # Check .env file
   PHOENIX_SPACE_ID=your-space-id
   PHOENIX_API_KEY=your-api-key
   PHOENIX_PROJECT_NAME=enterprise-cx-agent
   ```

### Session ID Not Persisting Across Turns

**Problem**: Each message creates a new session instead of continuing the conversation

**Solution**: Ensure the agent instance persists in Chainlit session
```python
# app.py - on_chat_start
cl.user_session.set("agent", SupportAgent())  # ✅ Creates once per session

# app.py - on_message
agent = cl.user_session.get("agent")  # ✅ Reuses same agent
response = agent.run(message.content)
```

### User ID Not Tracked

**Problem**: user.id attribute is not appearing in Arize

**Solution**: Ensure Chainlit authentication is enabled and user object exists
```python
user = cl.user_session.get("user")
if user:  # May be None if no authentication configured
    user_id = getattr(user, 'identifier', None)
```

## References

- **Arize Sessions Documentation**: https://arize.com/docs/ax/observe/tracing/sessions-and-users
- **OpenInference Instrumentation**: https://github.com/Arize-ai/openinference
- **Chainlit User Sessions**: https://docs.chainlit.io/concepts/user-session
- **OpenTelemetry Attributes**: https://opentelemetry.io/docs/specs/semconv/

## Next Steps

### Recommended Enhancements

1. **Session-Level Evaluations**
   - Create evaluators that assess entire conversations
   - Track metrics like "conversation success rate"
   - Identify patterns in failed conversations

2. **User Journey Analysis**
   - Use `user.id` to track users across multiple sessions
   - Analyze user behavior patterns
   - Identify power users vs. struggling users

3. **Session Tags**
   - Add tags for quick filtering (e.g., "escalated", "refund_processed")
   ```python
   with using_attributes(
       session_id=self.session_id,
       tags=["escalated", "vip_customer"]
   ):
   ```

4. **Session Metadata Enrichment**
   - Add business context to sessions
   ```python
   metadata = {
       "customer_tier": "VIP",
       "issue_type": "return",
       "resolution_time_seconds": 120
   }
   ```

## Summary

✅ **Session tracking is now fully implemented**
✅ **All Anthropic API calls are tracked with session context**
✅ **Sessions appear in Arize UI for conversation analysis**
✅ **User tracking is supported for cross-session analysis**
✅ **Rich metadata is captured for debugging and analytics**

You can now view full user-AI conversations grouped by session in the Arize UI, enabling comprehensive conversation analysis and performance monitoring.
