
---

# 2️⃣ AI Agent Workflow Diagram (LangGraph)

Add another diagram for the **AI reasoning pipeline**.

```markdown
## 🧠 LangGraph Agent Workflow

```mermaid
flowchart LR

A[Input URL] --> B[Content Extraction Agent]

B --> C[Policy Retrieval Agent]

C --> D[Compliance Evaluation Agent]

D --> E[Risk Analysis]

E --> F[Decision Engine]

F --> G[PDF Report Generator]
