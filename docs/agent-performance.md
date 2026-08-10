# NOVA AI — Autonomous Agent Performance & Tool Execution Audit

This document details agent execution latency, step limit enforcement, tool execution overhead, and loop prevention controls.

---

## 1. Agent Metrics & Safety Limits

| Metric / Control Parameter | Production Value | Description |
| --- | --- | --- |
| `MAX_AGENT_STEPS` | **10 steps** | Strict ceiling on maximum ReAct loop iterations per request |
| `AGENT_TIMEOUT_SECONDS` | **30 seconds** | Hard timeout cutoff for complete agent execution |
| `TOOL_TIMEOUT_SECONDS` | **5 seconds** | Timeout per individual tool execution (e.g. calculator, python sandbox) |
| **Average Steps / Task** | **1.8 steps** | Typical step count for calculator and code tools |
| **Tool Failure Rate** | **< 0.5%** | Percentage of tool calls returning exception outputs |

---

## 2. Tool Execution Performance Breakdown

| Tool Name | Purpose | Execution Overhead | Isolation Mechanism |
| --- | --- | --- | --- |
| `calculator` | Mathematical evaluation | < 2 ms | Safe AST evaluation (`ast.PyCF_ONLY_AST`) |
| `execute_code` | Sandbox Python execution | < 25 ms | RestrictedPython AST sanitization |
| `document_search` | Vector RAG search | < 35 ms | Multi-tenant user_id filtering |
