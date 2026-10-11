# Week 4 Individual Video Presentation — Script / Talking Points

5-10 minutes, covering the 10 required points (brief, Section 13).
Written to be read naturally or used as talking points, not read word
for word. Rough timing assumes normal speaking pace; adjust freely.

---

**1. The FinTrust problem** (~45 sec)

FinTrust Digital Bank is a fictional digital bank used for this
internship programme. The idea behind the project is that FinTrust
wants to use data, machine learning and generative AI to better
understand its customers and transactions, support risk-related
decisions, and strengthen its digital operations. My track's job
inside that is specifically about risk review: taking a transaction
and deciding whether it should be flagged for a human to look at.

**2. My assigned track** (~20 sec)

I was on the Machine Learning Engineering track. My job wasn't to
build the predictive model itself, that's Data Science's role, it was
to build the technical pipeline around it: the part that takes raw
data in, validates it, prepares it, feeds it to whatever model is
available, and returns a clean, structured prediction out. Reliable
plumbing, basically.

**3. What I personally developed** (~90 sec)

Over four weeks I built a full pipeline: Data, Validation,
Preprocessing, Feature Preparation, Model, Prediction, Output, and
Testing, exactly the stages I designed in Week 1. By Week 2 that was a
working repository with every stage implemented and a placeholder
model standing in for Data Science's, since nothing had been handed
over. In Week 3, since no Data Science model ever arrived, I trained
my own development model, a logistic regression, on the real FinTrust
data, and fixed a real bug I'd found in how the API was encoding
single transactions differently from a full batch. I also built a
FastAPI service on top so the pipeline can be called over a request
and response, not just run in batch. Week 4 was about finalizing all
of that: closing the one remaining gap in the API's error handling,
writing a full end to end test table, and bringing the documentation
to a genuinely final state.

**4. Tools used** (~15 sec)

Python, pandas, scikit-learn, joblib for saving the model, PyYAML for
config, pytest for testing, FastAPI for the service layer, and Git and
GitHub throughout.

**5. Key findings or results** (~60 sec)

The honest headline is that my development model's precision is low,
around 0.28, so a lot of what it flags as risky isn't. I'm not going
to dress that up. What I'd point to instead is that the pipeline
itself is solid: it runs cleanly end to end on all 12,000 real
transactions, it's reproducible, meaning the same input always gives
the same output, and the bug I found in Week 2, where a single
transaction could get encoded differently depending on how it arrived,
is genuinely fixed, not just documented as a known issue.

**6. Testing and validation** (~45 sec)

I ended the project with 40 automated tests, covering every stage of
the pipeline individually and the orchestrator as a whole: valid
input, missing values, unexpected categories, wrong data types, empty
input, model loading, prediction generation, output format, and
reproducibility. For Week 4 specifically I wrote an explicit table
showing each of those, what I expected, what actually happened, and
what I did about it, which is a brief requirement I wanted to show
properly rather than just saying "I tested it."

**7. Improvements made** (~30 sec)

The main one this week was the API. It used to let an unexpected error
leak a raw internal stack trace back to whoever called it. I added a
proper handler so now it always returns a clean, safe error instead,
and I added a test proving that.

**8. How my work connects to the wider FinTrust solution** (~40 sec)

In the overall FinTrust flow, my track sits in the middle: Predictive
Risk Intelligence and the ML Workflow or Service stage. I should be
honest here too, I never actually received anything from the Data
Science track to integrate, no model, no interface, nothing, across
all four weeks. So instead of pretending some handoff happened, I
documented that plainly and built the pipeline so that if a real model
ever does show up, it plugs into one clear interface without anything
else needing to change.

**9. Limitations** (~40 sec)

This is a prototype, not a production system. All the data is
synthetic. The risk label isn't a real fraud signal, it's an
educational target. My model's precision is weak. There's no
authentication on the API, no load testing, and it's only been
validated against one snapshot of data. I'd rather say all of that
clearly than have someone assume this is more finished than it is.

**10. Key lessons learned** (~40 sec)

Three things stuck with me. First, finishing well is a different skill
from building, Week 4 wasn't about adding features, it was about
checking what I already had actually held up. Second, disclosing a
weakness instead of hiding it made every following week easier,
because nothing was buried. And third, a stale assumption is cheap to
double check and expensive to carry into a final submission unchecked,
which is exactly what I did this week with the Data Science dependency
status.

---

**Closing line (optional):**

That's my FinTrust ML Engineering submission: a working, tested,
honestly-documented pipeline, built solo, finished properly. Thanks for
watching.
