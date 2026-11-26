---
title: Where did my IoT data go? Tracking it without tracking everything
theme: iiot
type: teardown
date: 2024-02
summary: You cannot follow every message from a sensor to a database. You do not need to. Here is a simple way to know where data goes missing.
tags: observability, MQTT, TimescaleDB, OpenTelemetry, data lineage
---
Think about a parcel. You can see each stop it passed through, so when it goes missing you know where to look.

Data from a sensor makes a similar trip. It leaves the sensor, passes through a **broker** (the post office for messages), then splits in two: a **live path** that feeds dashboards, and a **storage path** that keeps history. Both end up in a database. When a number is missing on a screen, the question is always the same: *where did it go?*

You could follow every single message the way a courier tracks a parcel. With thousands of messages a second, that costs far too much, and the tracking itself slows down the system it is watching. The good news is that you do not need it.

## The idea in one line

**Count everything. Follow a few. Keep the odd ones.**

<figure class="diagram"><svg viewBox="0 0 610 280" role="img" aria-label="A reading travels from a sensor through a broker, then a live path and a storage path, into a database. Three layers of tracking sit underneath: count everything, follow a few, always keep the odd ones." style="width:100%;height:auto;font-family:ui-monospace,Consolas,monospace"><rect x="10" y="32" width="100" height="40" rx="8" fill="#fff" stroke="#0a0a0a" stroke-width="3"/><text x="60.0" y="56.0" text-anchor="middle" font-size="12" font-weight="700" fill="#0a0a0a">SENSOR</text><rect x="150" y="32" width="100" height="40" rx="8" fill="#fff" stroke="#0a0a0a" stroke-width="3"/><text x="200.0" y="56.0" text-anchor="middle" font-size="12" font-weight="700" fill="#0a0a0a">BROKER</text><rect x="300" y="4" width="120" height="40" rx="8" fill="#fff" stroke="#0a0a0a" stroke-width="3"/><text x="360.0" y="28.0" text-anchor="middle" font-size="12" font-weight="700" fill="#0a0a0a">LIVE PATH</text><rect x="300" y="60" width="120" height="40" rx="8" fill="#fff" stroke="#0a0a0a" stroke-width="3"/><text x="360.0" y="84.0" text-anchor="middle" font-size="12" font-weight="700" fill="#0a0a0a">STORAGE PATH</text><rect x="470" y="32" width="130" height="40" rx="8" fill="#fff" stroke="#0a0a0a" stroke-width="3"/><text x="535.0" y="56.0" text-anchor="middle" font-size="12" font-weight="700" fill="#0a0a0a">DATABASE</text><path d="M110 52L150 52" stroke="#0a0a0a" stroke-width="3" fill="none" stroke-linecap="round"/><path d="M250 52L275 52" stroke="#0a0a0a" stroke-width="3" fill="none" stroke-linecap="round"/><path d="M275 24L275 80" stroke="#0a0a0a" stroke-width="3" fill="none" stroke-linecap="round"/><path d="M275 24L300 24" stroke="#0a0a0a" stroke-width="3" fill="none" stroke-linecap="round"/><path d="M275 80L300 80" stroke="#0a0a0a" stroke-width="3" fill="none" stroke-linecap="round"/><path d="M420 24L445 24" stroke="#0a0a0a" stroke-width="3" fill="none" stroke-linecap="round"/><path d="M420 80L445 80" stroke="#0a0a0a" stroke-width="3" fill="none" stroke-linecap="round"/><path d="M445 24L445 80" stroke="#0a0a0a" stroke-width="3" fill="none" stroke-linecap="round"/><path d="M445 52L470 52" stroke="#0a0a0a" stroke-width="3" fill="none" stroke-linecap="round"/><rect x="10" y="126" width="590" height="40" rx="8" fill="#ffde00" stroke="#0a0a0a" stroke-width="3"/><text x="305" y="151" text-anchor="middle" font-size="13" font-weight="700" fill="#0a0a0a">1. COUNT EVERYTHING · cheap: just totals</text><rect x="10" y="178" width="590" height="40" rx="8" fill="#fff" stroke="#0a0a0a" stroke-width="3"/><text x="305" y="203" text-anchor="middle" font-size="13" font-weight="700" fill="#0a0a0a">2. FOLLOW A FEW · a small, fixed sample</text><circle cx="60" cy="172" r="0" /><circle cx="170" cy="172" r="0" /><circle cx="300" cy="172" r="0" /><circle cx="430" cy="172" r="0" /><circle cx="540" cy="172" r="0" /><rect x="10" y="230" width="590" height="40" rx="8" fill="#0a0a0a" stroke="#0a0a0a" stroke-width="3"/><text x="305" y="255" text-anchor="middle" font-size="13" font-weight="700" fill="#ffde00">3. ALWAYS KEEP THE ODD ONES · errors, gaps, late data</text></svg><figcaption>One journey, three layers of tracking. Only the first one covers every message.</figcaption></figure>

## 1. Count everything

Give every message a number from the sensor: 1, 2, 3 and so on. Then, at each stop, write down just two things for each time window: how many arrived, and the lowest and highest number.

If the sensor sent 1 to 100 and the database holds 1 to 97, you know three are missing. Compare each stop with the next one and you can see exactly where they disappeared.

This is cheap. It is a few numbers per sensor, not a record for every message.

## 2. Follow a few

Pick a small group of messages and follow them the whole way, noting the time at every stop. This shows you how long each step takes and where the slow parts are.

How do you make sure every stop picks the *same* messages? Use the message's own number as a lottery ticket. Every stop applies the same rule to the same number and reaches the same answer, so nobody has to coordinate. A message that is picked is followed from the sensor all the way to the database.

## 3. Always keep the odd ones

Some things are too important to leave to chance, so always record them:

- **Errors**, and messages that could not be processed
- **Gaps**, where a number is missing
- **Late arrivals**, where a message shows up long after it was sent
- **Test messages.** A fake sensor sends a message every few seconds along the real route. If the test message gets through, the route works, even when real sensors are quiet.

## How much should you follow?

It depends on two questions. How many messages do you carry? And what happens if one is lost or late?

- **Few messages, each one important** (such as the stage changes in an autoclave cure cycle): follow all of them.
- **Lots of messages, connections that come and go** (such as vehicles): follow a small sample. Late data is normal here, so judge it against how long the vehicle was offline.
- **Regular readings from buildings:** counts and a check that each sensor is still reporting are usually enough.
- **Safety or regulated work:** keep a full record of the events you must be able to prove, and sample the rest.

Start small. Count everything, follow a few and keep the odd ones. Follow more only where missing a message would hurt.

## Three mistakes to avoid

- **Do not give every sensor its own chart line.** It makes monitoring bills explode. Group by type of sensor instead, and keep per-sensor detail in the counts.
- **Do not write the readings into the logs.** Log the message number and the reason, nothing more.
- **Do not use the sample to prove a message arrived.** The sample shows how things behave. The counts prove what arrived.

## Where each piece lives

Charts and alerts can go in Datadog or CloudWatch. The followed messages can go in OpenTelemetry. The counts can sit in TimescaleDB, next to the data they describe.

## When data goes missing, ask in this order

1. Do the counts match at every stop?
2. Which two stops stop matching?
3. Does the test message go missing too?
4. Is the data lost, or just late?
