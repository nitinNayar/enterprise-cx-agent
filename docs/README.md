# 📚 Documentation Index

Complete documentation for the Bookly intelligent returns agent with recommendation engine.

---

## 🎬 Demo & Testing

### [DEMO_GUIDE.md](./DEMO_GUIDE.md)
**Comprehensive testing guide with 6 detailed scenarios**
- Happy path with automatic exchange
- Policy enforcement scenarios
- Angry customer handling
- VIP exception testing
- What to watch for
- Common issues

**Use when:** You want detailed test scenarios with expected outcomes

---

### [QUICK_REFERENCE.md](./QUICK_REFERENCE.md)
**Copy-paste test scripts for quick validation**
- 4 core test scenarios
- Minimal instructions
- Quick validation checklist

**Use when:** You want fast copy-paste testing

---

## 🏗️ Implementation Details

### [EXCHANGE_WORKFLOW.md](../EXCHANGE_WORKFLOW.md)
**Automatic exchange feature documentation**
- Before/after comparison
- Tool implementation
- Service methods
- Example conversation flows
- Benefits and metrics

**Use when:** You want to understand how automatic exchange works

---

### [BEFORE_AFTER_FLOW.md](../BEFORE_AFTER_FLOW.md)
**Two-step approval flow (approval first, then offer)**
- Problem: pushy recommendations
- Solution: approve first, soft offer second
- Comparison table
- Customer experience impact

**Use when:** You want to understand the approval-first design

---

### [PERSONALIZATION_UPDATE.md](../PERSONALIZATION_UPDATE.md)
**Generic → specific recommendation messaging**
- Problem: "great taste in books" (generic)
- Solution: "loved thrillers by Lee Child" (specific)
- How personalization extraction works
- Examples for different genres

**Use when:** You want to understand personalized messaging

---

### [GREETING_BUG_FIX.md](../GREETING_BUG_FIX.md)
**Why agent wasn't greeting customers by name**
- Root cause analysis
- The fix: moved greeting protocol to top
- Before/after comparison
- Why it works

**Use when:** Agent skips greeting or you want to understand prompt structure

---

## 🔧 Technical Reference

### [TECHNICAL_OVERVIEW.md](../TECHNICAL_OVERVIEW.md)
**System architecture and technical details**
- Question routing system
- Specialized prompts
- Tool definitions
- Recommendation engine
- Precedent graph system

**Use when:** You want deep technical understanding

---

## 🚀 Quick Start

1. **First time?** Start with [QUICK_REFERENCE.md](./QUICK_REFERENCE.md)
2. **Want details?** Read [DEMO_GUIDE.md](./DEMO_GUIDE.md)
3. **How does X work?** Check implementation docs above
4. **Something broken?** Check relevant bug fix documentation

---

## 📋 Test Order Reference

| Order | Customer | Type | Use For |
|-------|----------|------|---------|
| ORD-123 | John McClane | Gold VIP | Happy path, exchange |
| ORD-456 | Jason Bourne | Regular | Policy denial |
| ORD-999 | Neo Anderson | Regular | Angry customer |
| ORD-777 | Sarah Connor | Platinum VIP | VIP exception |
| ORD-888 | Jack Ryan | Regular | Loyal customer |

---

## 🆘 Troubleshooting

**Connection errors?**
```bash
python diagnose_connection.py
```

**Agent not greeting?**
→ Read [GREETING_BUG_FIX.md](../GREETING_BUG_FIX.md)

**Generic recommendations?**
→ Read [PERSONALIZATION_UPDATE.md](../PERSONALIZATION_UPDATE.md)

**Pushy upsell?**
→ Read [BEFORE_AFTER_FLOW.md](../BEFORE_AFTER_FLOW.md)

**Manual exchange?**
→ Read [EXCHANGE_WORKFLOW.md](../EXCHANGE_WORKFLOW.md)

---

**Last Updated:** 2026-02-09
