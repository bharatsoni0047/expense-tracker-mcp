# STAR — Expense Tracker for your AI assistant

The problem, the decisions and what came out of them. See [README.md](README.md) to run it.

---

## Situation

Personal expense tracking has a well-known failure mode, and it is not a technical one.
The apps work. People stop using them.

The reason is friction. Recording a 120-rupee coffee means unlocking a phone, opening an
app, tapping "add", choosing a category from a dropdown, typing an amount, and saving. That
is perhaps twenty seconds of effort for a piece of information worth almost nothing on its
own — and it is only worth anything if you do it *every time*, which nobody sustains.

Meanwhile most people now have an AI assistant open for other reasons, and telling it
something costs a single sentence.

The technical situation is that assistants cannot do this on their own. A language model
has no memory between conversations and no way to write to a file. It can discuss your
spending, but it cannot record it, and next week it will not remember. Bridging that gap
needs a small program the assistant can call.

---

## Task

Build the smallest possible thing that removes the friction:

| Requirement | Why |
|---|---|
| **Recording must cost one sentence** | Any more and it will not be sustained — that is the whole problem. |
| **Data stays on the user's machine** | Spending is personal. It should not require trusting a third party. |
| **It must work with any assistant** | Tying it to one product means rebuilding it when the user switches. |

That last one is why this is built on the Model Context Protocol rather than as a plugin
for a specific assistant — the same server works with any client that speaks it.

---

## Action

### 1. Split it into the smallest useful set of capabilities

Four things, and deliberately no more:

- **Add** one entry
- **List** entries between two dates
- **Summarise** totals grouped by category
- **A category list**, exposed as a resource rather than a tool

The last one is the interesting design choice. The categories are not an action the
assistant performs — they are reference data it should *read* before deciding how to file
something. Exposing them as a resource rather than a tool means the assistant can consult
the taxonomy without a round trip, so "coffee" reliably becomes `food / coffee_tea` instead
of the model inventing a category name each time.

That is what keeps the data consistent enough to total up later. Without it, three months
of entries end up with `food`, `Food`, `eating`, and `restaurants` as four different
categories.

### 2. Made the database calls asynchronous

The straightforward version uses the standard synchronous SQLite library. It works, and it
blocks the event loop for the duration of every write.

For a single user that is invisible. I used `aiosqlite` anyway, because the failure it
prevents is the kind that appears only under conditions you cannot reproduce while
developing — a slow or contended disk turning a fast operation into a stall that freezes
everything else.

### 3. Kept initialisation synchronous, and made it fail early

Setup deliberately does not follow that pattern. It runs once, synchronously, at import —
and it performs a write test rather than only creating tables.

The reason: a read-only or full filesystem otherwise produces a server that starts cleanly
and fails on the user's first attempt to record something, at the exact moment they are
least willing to debug it. Failing at startup with a clear error is far better than failing
later.

### 4. Fixed the repository itself

Three problems that made the project look abandoned regardless of the code:

- **`expenses.db` was committed** — meaning actual spending data was published, and anyone
  cloning it started with someone else's entries.
- **A compiled cache file was committed.**
- **`.gitignore` was completely empty**, which is why both of the above happened.

The database is now untracked and ignored, along with the cache and the usual local files.
This is not interesting engineering, but a repository whose README was twelve bytes and
which shipped its own database file communicated something untrue about the code inside it.

---

## Result

| Outcome | Detail |
|---|---|
| **One sentence to record** | *"lunch, 340"* and it is filed correctly |
| **Consistent categories** | The taxonomy is read before filing, not invented per entry |
| **Fully local** | A SQLite file on the user's own machine; nothing uploaded |
| **Assistant-agnostic** | Any client speaking the protocol works |
| **A clean repository** | Personal data and build artefacts no longer committed |

### What I would tell an interviewer

This is a small project and I would not oversell it. Around 150 lines, four capabilities,
one file.

The decision worth discussing is exposing categories as a **resource** rather than a tool.
It is a distinction that is easy to skip, and skipping it produces a subtly broken system:
the assistant invents a plausible category each time, everything appears to work, and three
months later the totals are meaningless because the same expense was filed four different
ways. The category list is reference data the model should read, not an action it should
perform — and modelling it correctly is what makes the summaries trustworthy.

The second thing I would mention is what I found in the repository rather than the code.
The committed database file was real spending data, published publicly, because
`.gitignore` was empty. The code was fine. The repository was not. It taught me to check
what is actually *in* a repository separately from reviewing what the code does — they are
different failures with different causes.

### What I would do next

1. **Editing and deletion.** You can add, list and total, but a mistyped amount currently
   requires editing the database by hand. That is the most obvious missing capability.
2. **A durable default location.** The file lives in the system temporary directory, which
   some systems clear on reboot. It should default somewhere permanent.
3. **Currency support.** Amounts are plain numbers, so mixing currencies produces a total
   that means nothing.
4. **Budgets.** Recording is solved; the natural next question is *"am I over budget?"*,
   which needs a target to compare against.
