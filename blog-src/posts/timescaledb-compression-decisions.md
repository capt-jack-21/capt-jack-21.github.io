---
title: TimescaleDB compression: the decisions that actually mattered
theme: iiot
type: decision
date: 2026-11-26
summary: A decision record on chunking, segmenting and retention for telemetry that is written constantly and read in bursts.
tags: TimescaleDB, time-series, compression, retention
status: placeholder
---
Compression is easy to switch on and easy to get subtly wrong. The settings that matter are the ones that decide how data is grouped on disk, because they set how fast the common queries will be.

## Context
*[To be written: what kind of telemetry, how it is written, and how it is read.]*

## Options considered
| Decision | Option A | Option B |
|---|---|---|
| Chunk interval | *[ ]* | *[ ]* |
| Segment-by columns | *[ ]* | *[ ]* |
| One database or several | *[ ]* | *[ ]* |

## The call, and why
*[To be written.]*

## What it cost
*[To be written: the trade-offs that came with the choice.]*

## What I'd revisit
*[To be written.]*
