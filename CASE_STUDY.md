# Case study: a weekly support report from a helpdesk export

**Demo scenario. Puentara is a fictional company.** It is a money app for freelancers and small businesses with customers in the US and Latin America. Every ticket, customer and agent here is synthetic, and every number is sample data.

## The situation

Puentara's support lead runs a small team that answers tickets by email, chat and phone, in English and Spanish. The helpdesk can export every ticket to a CSV file. What it does not give the lead is a clear weekly picture.

## The problem

Every Monday the lead opens the export in a spreadsheet and tries to answer the same questions:

- Are we getting more tickets, or are we just slower?
- Which issues are growing this week?
- Which categories wait too long for a first reply, and are we meeting our targets?
- How many tickets are still open, and how old are they?
- Do Spanish-speaking customers wait longer than English-speaking ones?

Building that by hand takes hours. The export is messy: duplicate rows, a few broken dates, blank language fields, categories typed in Spanish by one agent and in English by another. The result also changes depending on who builds it that week. So when the lead asks for a Spanish-speaking agent, or explains why lost-card tickets need faster handling, it comes down to a gut feeling instead of a number everyone trusts.

## The solution

The lead drops the export into the tool and gets the same report every week.

From the command line, one command writes a summary in English or Spanish: key numbers, a few "what stands out" sentences, a data-quality note, and 10 tables as Markdown, HTML and CSV files that open in Excel with accents intact.

In the dashboard, the lead uploads the file, picks a date range and channels, and switches the whole page between English and Spanish. A Spanish-speaking team lead sees "Tickets abiertos por antigüedad" and "Sube tu exportación CSV", written with tú.

The tool also applies the rules a support team already lives by. A lost or stolen card is always measured against the urgent target (one hour, nights and weekends included), even if someone exported it as "low". The report shows counts, times, categories and ticket IDs only, never what the customer wrote, so a card number typed into a ticket can't end up in a slide deck.

## What was built

- Python with pandas for the cleaning and the numbers.
- A Streamlit dashboard using its built-in charts.
- A command-line report that writes Markdown, HTML and CSV, and needs no Streamlit.
- Every label in English and Spanish, in one strings file.
- A seeded script that makes about 1,200 synthetic Puentara tickets with known patterns and known mess.
- 137 automated tests, including checks that no ticket text, fake card number, CVV or one-time code reaches any output.

No AI, no API key and no account. It runs offline.

## What the demo shows (sample data)

Running the report on the synthetic Puentara export (12 weeks, 2026-08-03 to 2026-10-25):

- **Cleaning:** 1,201 rows read, 10 duplicate ticket IDs removed, 4 rows with unreadable dates skipped, 91 blank languages filled in, 6 lost-card tickets raised from "low" to urgent. 1,187 tickets used.
- **Key numbers:** median first reply 5.2 h, 78% of first replies within the SLA target, 39 open tickets, 39% of tickets in Spanish.
- **What stands out:**
  - Spanish tickets wait 1.9x as long as English ones for a first reply (median 7.2 h vs 3.7 h).
  - Failed or pending transfer tickets jumped to 51 in the week of 2026-09-14, compared with a typical 12.
  - The Spanish share went from 33% in the first 4 weeks to 47% in the last 4.
  - 18 open tickets are 7 or more business days old, all of them app bugs.

These patterns were **planted** by the data script so the report has something to find. They show that the tool finds them; they say nothing about a real team. Two details are worth being honest about:

- **The script planted 1.6x for Spanish, and the report shows 1.9x.** The script slows Spanish replies on each priority's own clock, which is business hours for most tickets. The report measures the wall-clock time the customer actually waited. A longer business-hours delay is more likely to run past closing time or into a weekend, and those hours count for the customer. That turns 1.6x into 1.9x. A real lead would want to know both numbers, which is why the report states how it measures.
- **"Card lost or stolen has the lowest SLA share: 70%" is not a finding.** Nobody planted it. Lost cards always get the strictest target, 60 minutes around the clock, and the planted Spanish slowness pushes many Spanish lost-card replies past that hour. Tax forms is at 71%, almost the same. On real data I would check this line before calling it a problem.

## Adapting it for a real team

- **Your export, your columns.** Send a sample export (a few rows with the text removed is enough). I add your helpdesk's column names and any custom category field to `config.py`. Zendesk and Freshdesk names are already covered.
- **Your categories and targets.** The nine Puentara categories, SLA targets, business hours and category floors all live in one settings file.
- **Your questions.** The "what stands out" rules are simple thresholds. We pick the ones that matter to your team, like a category growing week over week or a backlog older than your limit.
- **Your language mix.** English and Spanish are built in. Another language means another block in the strings file and an update to the language detector.
- **Your routine.** Today you run it by hand on a fresh export, or open the dashboard on Monday morning. A scheduled run could be added if your team needs one.

Send me a recent export with the ticket text removed, and I'll show you what your first report would look like.
