---
title: Protocol normalisation is the real IIoT problem
theme: iiot
type: opinion
date: 2026-11-26
summary: Getting data off a device is easy. Making a hundred different devices mean the same thing to the platform is the hard part.
tags: OPC UA, MQTT, BACnet, Modbus, data modelling
status: placeholder
---
Connecting to a device is a solved problem. Every protocol has a library, and a demo that reads one register takes an afternoon. The work that decides whether a platform survives is what happens *after* the read: names, units, scaling, quality flags and context.

## The argument
*[To be written: the core opinion in two or three sentences.]*

## Where it breaks in practice
- Point names that only make sense to the engineer who commissioned the site
- Units and scaling that live in a spreadsheet, not in the data
- The same physical quantity arriving over different protocols with different semantics
- Quality and staleness: a value that is old is not the same as a value that is zero

## What a normalisation layer has to own
*[To be written: the responsibilities of the canonical layer, and what it should refuse to do.]*

## What I'd do differently
*[To be written from real project experience.]*
