## **The Use Case: "The Transparent Precedent Engine"**

This system solves the "Black Box" problem in AI. Typically, when an AI makes a decision, it's hard to trace *why*. In this use case, we bridge human authority (VP emails) with AI actions (Chatbot returns).

**The scenario in action:**

1. **Standard Denial:** A customer requests a return for a TV bought 45 days ago (Policy = 30 days). The Bot initially denies the request.
2. **External Input:** Behind the scenes, a VP sends an email: *"Approve all electronics returns for 60 days during the holiday period."*
3. **Graph Update:** The system extracts this and creates a `Decision` node in **Kùzu** linked to the `VP` node.
4. **Logging the Logic:** Every step—from reading the email to updating the graph—is logged with a timestamp and "Reasoning" tag.
5. **Autonomous Approval:** The next time a customer asks, the Bot queries the graph, finds the VP's precedent, and approves the return.
6. **The Audit Trail:** If a manager asks months later, "Why did the bot approve this late return?", the **Logs** provide a line-by-line receipt of the specific VP email that triggered the change.

---

## **1. Functional Requirements**

### **A. Logging & Observability (The "Receipts")**

* **Decision Attribution:** Every time the AI Agent overrides a standard policy, it must log the specific `Decision ID` and `Person ID` from the graph that authorized the action.
* **Traceable Reasoning:** Use **Python's `logging` module** to record:
* **INFO Level:** Key milestones (e.g., "New VP ruling ingested," "Precedent found for Customer X").
* **DEBUG Level:** The raw Cypher queries sent to Kùzu and the JSON output from Claude.
* **WARNING Level:** When a decision is nearing its `expires_at` date or when a non-VP attempts an override.


* **Audit Persistence:** Logs should be formatted in JSON or structured text to be easily ingested by monitoring tools (like ELK or Datadog).

### **B. Data Structure (Kùzu Nodes & Objects)**

| Node Type | Key:Value Properties |
| --- | --- |
| **`Person`** | `name` (PK), `role` (e.g., VP), `department`, `last_active` |
| **`Decision`** | `id` (PK), `context`, `outcome`, `reasoning`, `source_ref`, `expires_at` |
| **`Product`** | `category_name` (PK), `risk_level` |

### **C. Intelligent Extraction (Claude 3.5 Sonnet)**

* **Entity Linking:** Extract unstructured text into the node properties above.
* **Confidence Scoring:** Log the "confidence" level of the LLM extraction; if Claude is unsure of the VP's intent, the system must log a `WARNING` and require human verification.

---

## **2. Technical Requirements**

### **A. Environment & Performance**

* **Database:** **Kùzu** for persistent, relationship-based storage.
* **Logic Engine:** **Claude 3.5 Sonnet** for parsing complex business nuance.
* **Language:** Python 3.10+ with strict type hinting.
* **Query Speed:** Graph traversals must complete in <200ms to avoid "lag" in customer chat.

### **B. Logging Implementation**

* **Standardized Format:** `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
* **Centralized Config:** A single `logging_config.py` module to ensure consistent logs across the Ingestor (Email side) and the Agent (Customer side).

---

## **3. Success Metrics for the Demo**

1. **Visibility:** Can you open the `app.log` file and see the exact moment the "Holiday Policy" was created?
2. **Override Logic:** Does the AI Agent successfully cite a VP's name in its internal logs when it changes a "No" to a "Yes"?
3. **Visualization:** Does the graph accurately show the link between the `Person (VP)` and the `Decision (60-day Return)`?

