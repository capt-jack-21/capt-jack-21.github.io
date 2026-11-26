---
title: What an AI agent gets wrong about building telemetry
theme: ai
type: problem
date: 2026-11-26
summary: Agents are fluent about data they do not understand. Units, point naming and stale readings are where they fail first.
tags: agents, grounding, Haystack, tool use, evals
status: placeholder
---
An agent that answers a question about a building with total confidence and a wrong unit is worse than no agent. The failures are rarely about the model. They come from the data it is handed.

## Symptom
*[To be written: a concrete wrong answer the agent gave.]*

## What I checked first
*[To be written.]*

## Root cause
Likely candidates to confirm against the real case: ambiguous point names, missing units, stale values treated as current, and equipment relationships that were never modelled.

## The fix
*[To be written: grounding through an ontology, tool design, or both.]*

## What I'd do differently
*[To be written.]*
