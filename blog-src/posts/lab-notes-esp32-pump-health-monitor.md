---
title: PumpSentinel: an ESP32 that watches a pump and raises its own work order
theme: robotics
type: lab
date: 2026-06-10
summary: A pump's motor current tells you when it is sick. An ESP32-S3 learns what normal looks like, names the fault, and opens a maintenance job without the cloud or an engineer.
tags: ESP32-S3, Isolation Forest, ESP-NOW, LVGL, edge AI, condition monitoring
---
A pump rarely fails without warning. Before it goes, the motor works harder or differently, and you can see that in the electric current it draws. PumpSentinel is my bench build that listens to that current, decides whether the pump looks healthy, and, if it does not, asks for a maintenance job to be created. It runs on an ESP32-S3.

## Listen to the motor, not the pump

One clamp-on current sensor goes around the supply line. Nothing is cut and nothing goes inside the pump. The idea is simple: the load tells the story. A pump running dry, one swallowing mud and one with a locked rotor each change how much current the motor draws.

The sensor is sampled 1,000 times a second. Every 400 samples form a window, and windows overlap by half. Each window is boiled down to five numbers: RMS current (the average strength), peak current, crest factor (how spiky the wave is), rate of change, and zero-crossing rate.

## Three layers on one chip

No single check catches everything, so there are three, and each covers what the others miss.

- **Self-calibration at boot.** The first 32 samples at normal load build the model in memory. There is nothing to configure.
- **Layer 1, Z-score.** Flags a sudden jump away from the baseline the pump set at boot.
- **Layer 2, Isolation Forest.** This is the machine learning part. It is unsupervised, with 10 small trees of depth 8, reading RMS, crest factor and rate of change. It gives an anomaly score from 0.0 to 1.0. It needs no labelled faults and no rules to write.
- **Layer 3, signature match.** Current zones put a name on the problem.

All of it runs on the one ESP32-S3, spread across both cores with FreeRTOS tasks.

## Current zones, named faults

| Current | What it means |
| --- | --- |
| 1.5 A or less | Dry run. No load, flagged at once. |
| 5.0 to 6.6 A | Normal for this pump. |
| 6.7 to 7.0 A | Warning. Load is climbing. |
| 7.1 to 7.5 A | Mud ingestion. Heavy, gritty load. |
| 7.6 A or more | Rotor stall. Confirmed fault. |

These zones were calibrated on a bench load bank with one pump. For your own motor, recalibrate for its current range. The numbers mean something only against how that pump behaves when healthy.

## From stall to work order

The sensor node and the touchscreen talk over ESP-NOW, a direct ESP32-to-ESP32 link with no router in between. The screen is a 4.3 inch touch HMI drawn with LVGL, showing health score, RMS current, crest factor, rate of change and anomaly score live.

When a rotor stall is confirmed and held past its debounce window:

1. The node joins WiFi and posts an alert to a webhook (an n8n workflow in this build).
2. The workflow opens a reactive maintenance job in the CAFM system.
3. The job id and number come back over ESP-NOW to the HMI.
4. The operator sees the job on the HMI's CAFM tab.

A 30 minute cooldown stops duplicate jobs. Everything before the stall runs with no router and no internet, which is the point of doing the thinking at the edge.

## Caveats

This is a working prototype, not a certified safety system. It was tested on a bench with one pump.

## Read the code

Firmware for both nodes, the ESP-NOW protocol and the HMI are open source under the MIT licence at github.com/capt-jack-21/pumpsentinel. Built with ESP-IDF, FreeRTOS, ESP-NOW, LVGL v8, an Isolation Forest and an n8n webhook.
