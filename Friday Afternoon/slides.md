---
theme: default
title: Quotation Bot
info: AI-powered quotation processing
drawings:
  persist: false
transition: slide-left
---

# Quotation Bot — Presentation

## Slide 1 — Introduction

### Quotation Bot

**An AI-powered assistant for faster and smarter quotation processing**

Quotation Bot receives customer emails, understands quotation requests,
researches products, and prepares quotation drafts for human review.

**Technology:** PydanticAI, FastAPI, React, SQLite, and ChromaDB.

---

## Slide 2 — The Problem

- Companies receive many different types of emails every day.
- Important customer messages can be buried in a busy inbox.
- A quotation request may require immediate attention because the potential
  customer could choose another supplier.
- Staff must manually search, read, understand, and prioritize each message.
- Product availability and pricing may require checking several systems.
- Missing or delaying one quotation can mean losing a valuable sales
  opportunity.

---

## Slide 3 — Value Proposition

Quotation Bot helps businesses:

- Find important quotation requests before they are overlooked.
- Process customer requests faster.
- Reduce repetitive inbox and data-entry work.
- Identify quotation details automatically.
- Search product information more efficiently.
- Keep a human reviewer in control before a quotation is sent.
- Preserve the agent's progress when human clarification is needed.

This frees sales and administrative staff to focus on other important work
without missing potential customers.

---

## Slide 4 — The Solution

1. Retrieve customer emails.
2. Classify emails as quotation requests or unrelated messages.
3. Extract products, quantities, and customer requirements.
4. Research companies and search the product catalogue.
5. Check inventory and calculate pricing.
6. Generate a quotation draft.
7. Allow a human to approve, edit, reject, or request changes.

The system uses SQLite as its source of truth and ChromaDB for semantic product
search.

---

## Slide 5 — Target Market

Quotation Bot is designed for small and medium-sized businesses that receive
many product or service enquiries by email, especially:

- Packaging and manufacturing companies.
- Wholesalers and distributors.
- Sales and procurement teams.
- Businesses without a dedicated quotation automation system.

The initial example focuses on a packaging company and its product catalogue.

---

## Slide 6 — Business Model

A possible future model would be:

- Monthly subscription based on the number of quotation requests processed.
- Higher plans for larger product catalogues and multiple users.
- Optional setup and integration services for email, inventory, and pricing
  systems.

The main business value would come from saving staff time and improving
quotation response speed.

---

## Slide 7 — Team

### Project Team

- **Ahmet:** Internet search and external research tool.
- **Shuyin:** Database design and data generation.
- **Baffour:** Core AI agent and quotation workflow.

The team combines AI, backend services, databases, and frontend development to
solve a practical business problem.

---

## Slide 8 — Call to Action

### From email request to reviewed quotation

Quotation Bot shows how AI can support sales teams without removing human
oversight.

**Next steps:**

- Test with more realistic business emails.
- Improve product and pricing integrations.
- Add authentication and user roles.
- Connect approved drafts to email sending.
- Measure time saved and quotation accuracy.

**Thank you.**