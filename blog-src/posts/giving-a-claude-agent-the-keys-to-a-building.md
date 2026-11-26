---
title: Giving a Claude agent the keys to a building, safely
theme: ai
type: teardown
date: 2026-03-25
summary: How to let an AI agent answer real questions about a building without letting it guess, break things or make numbers up.
tags: Claude, tool use, MCP, building automation, Haystack, agents, evals
---
A building operator asks: *"Why is the third floor too warm?"*

Answering takes real work. Someone has to find the right air handler, read its temperature and valve position, check the schedule, look at recent alarms, and compare it with the room readings. It is exactly the kind of multi-step question an AI agent is good at, and exactly the kind where a confident wrong answer does harm.

This post is about how to set the agent up so it gets the answer from the building, not from its imagination. It is the design behind my Building Ops Copilot, which pairs Claude with controlled tools and structured building data.

## How the agent works, in plain words

Claude does not touch the building. It can only ask for things, and your code decides what happens next.

<figure class="diagram"><svg viewBox="0 0 500 190" role="img" aria-label="The agent loop. An operator asks a question. Claude decides which tool to use. Your code runs the tool against the building data. The result goes back to Claude, and the loop repeats until Claude has enough to answer." style="width:100%;height:auto;font-family:ui-monospace,Consolas,monospace"><defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10Z" fill="#0a0a0a"/></marker></defs><rect x="10" y="20" width="140" height="46" rx="8" fill="#fff" stroke="#0a0a0a" stroke-width="3"/><text x="80" y="47" text-anchor="middle" font-size="12" font-weight="700" fill="#0a0a0a">1 OPERATOR ASKS</text><rect x="180" y="20" width="140" height="46" rx="8" fill="#ffde00" stroke="#0a0a0a" stroke-width="3"/><text x="250" y="47" text-anchor="middle" font-size="12" font-weight="700" fill="#0a0a0a">2 CLAUDE DECIDES</text><rect x="350" y="20" width="140" height="46" rx="8" fill="#fff" stroke="#0a0a0a" stroke-width="3"/><text x="420" y="47" text-anchor="middle" font-size="12" font-weight="700" fill="#0a0a0a">3 ASKS FOR A TOOL</text><rect x="10" y="130" width="140" height="46" rx="8" fill="#0a0a0a" stroke="#0a0a0a" stroke-width="3"/><text x="80" y="157" text-anchor="middle" font-size="12" font-weight="700" fill="#ffde00">ANSWER</text><rect x="180" y="130" width="140" height="46" rx="8" fill="#fff" stroke="#0a0a0a" stroke-width="3"/><text x="250" y="157" text-anchor="middle" font-size="12" font-weight="700" fill="#0a0a0a">5 BUILDING DATA</text><rect x="350" y="130" width="140" height="46" rx="8" fill="#fff" stroke="#0a0a0a" stroke-width="3"/><text x="420" y="157" text-anchor="middle" font-size="12" font-weight="700" fill="#0a0a0a">4 CODE RUNS IT</text><path d="M150 43H178" stroke="#0a0a0a" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#a)"/><path d="M320 43H348" stroke="#0a0a0a" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#a)"/><path d="M420 66V128" stroke="#0a0a0a" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#a)"/><path d="M350 153H322" stroke="#0a0a0a" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#a)"/><path d="M250 130V68" stroke="#0a0a0a" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="2 8" marker-end="url(#a)"/><text x="260" y="104" font-size="11" fill="#0a0a0a">result goes back</text><path d="M200 66V92H80V128" stroke="#0a0a0a" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#a)"/><text x="92" y="86" font-size="11" fill="#0a0a0a">when it has enough</text></svg><figcaption>The loop: Claude chooses, your code does, the result goes back. It repeats until Claude can answer.</figcaption></figure>

1. The operator asks a question.
2. Claude reads it and decides it needs more information, so it asks to use one of the tools you gave it.
3. **Your code** runs that tool against the building data and sends the result back.
4. Claude looks at the result. If it needs more, it asks for another tool. If not, it writes the answer.

That loop is the whole idea. Everything below is about making each step safe and accurate.

## Step 1: Give it tools, not access

A tool is a small, named action with a clear description, and Claude reads the description to decide when to use it. Here is one:

```json
{
  "name": "get_latest_value",
  "description": "Latest reading for one point on one piece of equipment. Returns the value, its unit and how old it is.",
  "input_schema": {
    "type": "object",
    "properties": { "point_id": { "type": "string" } },
    "required": ["point_id"]
  }
}
```

Notice what the tool does **not** do. It cannot run a free-form database query or open a connection to the control system. It does one narrow thing and always returns the unit and the age of the value, so the model never has to guess either.

A good starter set for a building:

- **Find:** find equipment and points by name or by relationship
- **Read:** latest value, history over a time range, active alarms, schedule
- **Explain:** what is this equipment, what feeds it, what does it serve

## Step 2: Make it look things up first

The most common failure is the agent inventing a point name that looks right. Block that by putting a **building model** between the question and the data.

In my Smart Building AI project, the chain is: the question goes to an ontology engine built on Project Haystack, which turns "air handler 3" into a validated piece of equipment with its real points. Only then do tools fetch data, and only then does the model answer. The model never gets to make up an identifier, because the lookup step either finds it or says it does not exist.

## Step 3: Separate looking from doing

Not all tools are equal.

| Kind | Example | Rule |
|---|---|---|
| Read | Latest value, history, alarms | Allowed freely, with limits on how much data one call can pull |
| Suggest | "Raise this setpoint by one degree" | The agent proposes it and shows its reasoning |
| Act | Actually change a setpoint | Only after a person approves, and always logged |

Start read-only. Add actions later, one at a time, only where the gain is clear.

## Step 4: Use what Claude gives you

A few features of working with Claude are especially useful here:

- **Tool use with schemas:** each tool is described with a typed input, so bad calls are easy to reject before they reach your system.
- **A system prompt for the building's rules:** things like "always state the unit", "say when a value is stale", and "never infer a reading you did not fetch".
- **Streaming:** show the answer and the tool steps as they happen, so an operator sees what the agent is doing instead of waiting.
- **MCP (Model Context Protocol):** expose the same tools through a standard interface, so other Claude clients can use them without rewriting the integration.

## Step 5: Test it like software

An agent that sounds right is not an agent that is right. Build a set of questions where the correct answer is known, and score the agent against it. A deterministic engine is perfect for this: in my Haystack engine, the answers come from rules, not from a model, so they serve as ground truth for counting how often the model gets it wrong.

Run that set every time you change a prompt, a tool description or the model. If the score drops, you find out before an operator does.

## Trade-offs

- **Speed:** several tool calls mean several round trips. Streaming helps the experience but not the total time.
- **Cost:** each loop sends context back to the model, so keep tool results small and focused.
- **Too many tools:** the more tools you offer, the more chances the agent picks the wrong one. Fewer, sharper tools work better.
- **Over-trust:** a smooth answer lowers the operator's guard. Show the evidence, meaning the readings and their ages, next to the answer.

## When the agent is wrong, check this first

1. Did it call the right tool, or skip one it needed?
2. Did the lookup step find the equipment, or did the model guess a name?
3. Was a value stale, or missing its unit?
4. Does the evaluation set cover this kind of question?
