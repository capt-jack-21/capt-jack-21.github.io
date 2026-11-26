---
title: Out-of-order events quietly corrupt your digital twin
theme: iiot
type: problem
date: 2026-11-26
summary: In an autoclave or a telematics unit, the order of events is part of what they mean. A counter beside the timestamp is how the platform knows what really happened.
tags: digital twin, event ordering, sequence numbers, MQTT, telematics, autoclave
---
Some events only make sense in order. Take an industrial autoclave that cures composite parts. The part goes through a controlled profile of temperature, pressure and vacuum: ramp, dwell, cool. A digital twin follows those stages and decides what is true about the part right now. If "cool" is processed before "dwell", the twin has the cure going backwards, and every decision built on that state (an alert, a quality release, a batch record) is built on something that did not happen.

A telematics unit has the same weakness. "Ignition off" processed ahead of the last position report ends the trip early. A harsh-braking event that lands after the trip closed gets attached to the wrong journey.

The rule that follows: **for these systems, the order of events is part of the data, and the platform has to be able to prove it.**

## Why events arrive out of order

Nothing has to be broken for this to happen. Everyday behaviour is enough:

- A device loses its connection, buffers events, and replays them later, mixed with fresh ones.
- A gateway or modem stores and forwards over a different path from live traffic.
- A broker with several partitions, or a pool of parallel consumers, processes messages at different speeds.
- At-least-once delivery means retries, so the same event can arrive twice.

Every hop can look in-order on its own while the whole path is not.

## Why a timestamp is not enough

The obvious fix is to sort by timestamp. It helps, but it cannot carry the whole job:

- Device clocks drift, start from zero after a cold boot, and jump when they finally sync.
- Two events can share the same millisecond.
- The platform's ingest time says when something arrived, not when it happened.

A timestamp says roughly *when*. It does not say what came *before* what.

## The fix: a counter beside the timestamp

Every event carries four things, written by the device at the moment of the reading:

| Field | What it is for |
|---|---|
| Source ID | Which device or unit the sequence belongs to |
| Session (boot) number | Tells a restart apart from a replay, so the counter can safely start again |
| Sequence number | Increments by one for every event from that source in that session |
| Timestamp + telemetry | When it was measured, and the reading itself |

The counter gives the platform something a clock cannot: certainty about order and about what is missing.

<figure class="diagram"><svg viewBox="0 0 640 276" role="img" aria-label="Events sent in order 1 to 4 arrive as 1, 3, 2, 4. A twin that trusts arrival order goes backwards to DWELL after COOL. A twin that checks sequence numbers keeps COOL, records the hole at 2 and stores the late event in history only." style="width:100%;height:auto;font-family:ui-monospace,Consolas,monospace"><text x="8" y="39" font-size="11" font-weight="700" fill="#0a0a0a">SENT</text><rect x="150" y="14" width="104" height="40" rx="8" fill="#fff" stroke="#0a0a0a" stroke-width="3"/><text x="202" y="31" text-anchor="middle" font-size="12" font-weight="700" fill="#0a0a0a">RAMP</text><text x="202" y="46" text-anchor="middle" font-size="10" fill="#0a0a0a">seq 1</text><rect x="270" y="14" width="104" height="40" rx="8" fill="#fff" stroke="#0a0a0a" stroke-width="3"/><text x="322" y="31" text-anchor="middle" font-size="12" font-weight="700" fill="#0a0a0a">DWELL</text><text x="322" y="46" text-anchor="middle" font-size="10" fill="#0a0a0a">seq 2</text><rect x="390" y="14" width="104" height="40" rx="8" fill="#fff" stroke="#0a0a0a" stroke-width="3"/><text x="442" y="31" text-anchor="middle" font-size="12" font-weight="700" fill="#0a0a0a">COOL</text><text x="442" y="46" text-anchor="middle" font-size="10" fill="#0a0a0a">seq 3</text><rect x="510" y="14" width="104" height="40" rx="8" fill="#fff" stroke="#0a0a0a" stroke-width="3"/><text x="562" y="31" text-anchor="middle" font-size="12" font-weight="700" fill="#0a0a0a">DONE</text><text x="562" y="46" text-anchor="middle" font-size="10" fill="#0a0a0a">seq 4</text><text x="8" y="109" font-size="11" font-weight="700" fill="#0a0a0a">ARRIVED</text><rect x="150" y="84" width="104" height="40" rx="8" fill="#fff" stroke="#0a0a0a" stroke-width="3"/><text x="202" y="101" text-anchor="middle" font-size="12" font-weight="700" fill="#0a0a0a">RAMP</text><text x="202" y="116" text-anchor="middle" font-size="10" fill="#0a0a0a">seq 1</text><rect x="270" y="84" width="104" height="40" rx="8" fill="#fff" stroke="#0a0a0a" stroke-width="3"/><text x="322" y="101" text-anchor="middle" font-size="12" font-weight="700" fill="#0a0a0a">COOL</text><text x="322" y="116" text-anchor="middle" font-size="10" fill="#0a0a0a">seq 3</text><rect x="390" y="84" width="104" height="40" rx="8" fill="#fff" stroke="#0a0a0a" stroke-width="3"/><text x="442" y="101" text-anchor="middle" font-size="12" font-weight="700" fill="#0a0a0a">DWELL</text><text x="442" y="116" text-anchor="middle" font-size="10" fill="#0a0a0a">seq 2</text><rect x="510" y="84" width="104" height="40" rx="8" fill="#fff" stroke="#0a0a0a" stroke-width="3"/><text x="562" y="101" text-anchor="middle" font-size="12" font-weight="700" fill="#0a0a0a">DONE</text><text x="562" y="116" text-anchor="middle" font-size="10" fill="#0a0a0a">seq 4</text><text x="8" y="179" font-size="11" font-weight="700" fill="#0a0a0a">BY ARRIVAL</text><rect x="150" y="154" width="104" height="40" rx="8" fill="#fff" stroke="#0a0a0a" stroke-width="3"/><text x="202" y="171" text-anchor="middle" font-size="12" font-weight="700" fill="#0a0a0a">RAMP</text><text x="202" y="186" text-anchor="middle" font-size="10" fill="#0a0a0a">stage ok</text><rect x="270" y="154" width="104" height="40" rx="8" fill="#fff" stroke="#0a0a0a" stroke-width="3"/><text x="322" y="171" text-anchor="middle" font-size="12" font-weight="700" fill="#0a0a0a">COOL</text><text x="322" y="186" text-anchor="middle" font-size="10" fill="#0a0a0a">stage ok</text><rect x="390" y="154" width="104" height="40" rx="8" fill="#0a0a0a" stroke="#0a0a0a" stroke-width="3"/><text x="442" y="171" text-anchor="middle" font-size="12" font-weight="700" fill="#ffde00">DWELL</text><text x="442" y="186" text-anchor="middle" font-size="10" fill="#ffde00">went backwards</text><rect x="510" y="154" width="104" height="40" rx="8" fill="#fff" stroke="#0a0a0a" stroke-width="3"/><text x="562" y="171" text-anchor="middle" font-size="12" font-weight="700" fill="#0a0a0a">DONE</text><text x="562" y="186" text-anchor="middle" font-size="10" fill="#0a0a0a">stage ok</text><text x="8" y="249" font-size="11" font-weight="700" fill="#0a0a0a">WITH SEQ</text><rect x="150" y="224" width="104" height="40" rx="8" fill="#fff" stroke="#0a0a0a" stroke-width="3"/><text x="202" y="241" text-anchor="middle" font-size="12" font-weight="700" fill="#0a0a0a">RAMP</text><text x="202" y="256" text-anchor="middle" font-size="10" fill="#0a0a0a">stage ok</text><rect x="270" y="224" width="104" height="40" rx="8" fill="#fff" stroke="#0a0a0a" stroke-width="3"/><text x="322" y="241" text-anchor="middle" font-size="12" font-weight="700" fill="#0a0a0a">COOL</text><text x="322" y="256" text-anchor="middle" font-size="10" fill="#0a0a0a">hole at seq 2</text><rect x="390" y="224" width="104" height="40" rx="8" fill="#ffde00" stroke="#0a0a0a" stroke-width="3"/><text x="442" y="241" text-anchor="middle" font-size="12" font-weight="700" fill="#0a0a0a">DWELL</text><text x="442" y="256" text-anchor="middle" font-size="10" fill="#0a0a0a">history only</text><rect x="510" y="224" width="104" height="40" rx="8" fill="#fff" stroke="#0a0a0a" stroke-width="3"/><text x="562" y="241" text-anchor="middle" font-size="12" font-weight="700" fill="#0a0a0a">DONE</text><text x="562" y="256" text-anchor="middle" font-size="10" fill="#0a0a0a">stage ok</text></svg><figcaption>The same four events. Only the version that checks sequence numbers survives the reordering.</figcaption></figure>

## What the platform does with it

For each source it remembers the last applied session and sequence, and decides:

- **Next in line:** apply it to the twin.
- **Duplicate:** the same session and sequence again, so drop it. This makes retries harmless.
- **Stale:** a lower sequence than the one already applied. Keep it in history for analysis, but never let it overwrite the current state.
- **Gap:** a jump of more than one. Apply it if the use case allows, and record the hole, so the twin knows it is missing something and can flag its own confidence.

```ts
type Evt = { src: string; epoch: number; seq: number; ts: string; data: unknown };
type Last = { epoch: number; seq: number };

function decide(last: Last | undefined, e: Evt): "apply" | "duplicate" | "stale" | "gap" {
  if (!last || e.epoch > last.epoch) return "apply";   // first event, or a new boot session
  if (e.epoch < last.epoch) return "stale";
  if (e.seq === last.seq) return "duplicate";
  if (e.seq < last.seq) return "stale";
  return e.seq === last.seq + 1 ? "apply" : "gap";      // gap: apply, but record the hole
}
```

For decisions that must not be wrong, add a short **reorder buffer**: hold a gap for a brief window so the missing event can arrive, then release in order. If it never arrives, proceed and mark the hole.

## Trade-offs

- **Device cost:** the counter and session number have to live on the device, and the session number must survive a reboot. That is a firmware change, not just a cloud change.
- **Latency vs correctness:** a reorder buffer adds delay. An autoclave stage change should wait for correctness. A live vehicle position can just take the latest.
- **Order is per source:** a counter orders one device's events. Across devices there is no global order, and timestamps with a tolerance are the best you have.
- **Keep the timestamp:** the counter does not replace it. Time-series storage and analytics still need real time.

## When a twin looks wrong, check this first

1. Are there gaps in the sequence for that source?
2. Are duplicates being applied twice?
3. Did the session number change (a reboot) and get mishandled?
4. Did the device clock jump around the time it went wrong?

Most "the twin is lying" problems turn out to be one of these four.
