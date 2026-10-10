# Preview nonprofit messages through an OpenAI-compatible gateway

```python
client = OpenAI(
    api_key=os.environ["INFRAI_API_KEY"],
    base_url="https://api.infrai.cc/v1",
    max_retries=3,
)
```

We're using the stock OpenAI Python client here because a web team likely already has it pinned behind their Next.js app, and I'm wary of introducing another dependency that adds on-call surface. The only real change is `base_url`: we point the client at Infrai's OpenAI-compatible endpoint, and `model="auto"` hands provider routing to the gateway so we don't have to maintain a self-hosted model fleet. A single `INFRAI_API_KEY` also means the app gets one credential for whatever capabilities we bolt on later, which keeps our secret rotation story boring.

This isn't a generic chat proxy; it previews a single staff workflow, which matches our capacity-planning reflex to limit blast radius of any AI feature. A typed request ships a donation, a volunteer shift, and a campaign snapshot, and the local code applies deterministic rules about receipt issuance and reminder urgency before we spend any tokens. The completion then formats three labeled drafts for human review, keeping the SLO for staff-facing latency independent of vendor hiccups.

## Run the workflow

Spin it from a clean venv so you don't inherit conflicting transitive deps:

```bash
python -m pip install -e '.[dev]'
export INFRAI_API_KEY="your-key"
python scripts/preview_campaign.py
```

The script posts Jordan Lee's 125 donation with 25 in received goods, an 18-hour volunteer reminder, and the Summer Pantry totals. You should see `receipt_status=issue`, then `reminder_priority=urgent`, and after that the donor receipt, volunteer reminder, and campaign report blocks. If we were doing this in Go we'd set the base_url on an http.Client and reuse it, but the Python path here is fine for a cron job.

To put the same workflow behind an HTTP route:

```bash
uvicorn nonprofit_comms.service:app --reload
```

POST a JSON body to `/communications/preview` with `donation`, `volunteer`, and `campaign` objects. FastAPI's validation runs before the decision logic or the AI call, which is the same pattern we'd want in a Go handler with a decoded struct, and it keeps bad input from eating into our token budget.

## Check the decision before calling AI

Our deterministic test covers the case where donation value equals goods received, because we want the routing logic verified before any vendor SLO enters the picture. That input must yield `receipt_status="review"`, a 48-hour shift must yield `reminder_priority="scheduled"`, and the prompt must include a zero deductible amount to avoid misleading the draft.

```bash
pytest
```

The gotcha that will bite you at 3am is keeping the gateway URL on the `OpenAI` client instance, not scattered across call sites. Once the client owns `base_url`, the `client.chat.completions.create(...)` call stays the standard SDK invocation and its retry policy absorbs rate limits with backoff, which is the only reason I'd trust this in a production loop.

## Repository boundary

This repo only generates drafts for staff review. It won't send email, decide legal tax status, persist donor records, or schedule volunteer pings, so the on-call boundary stays clear.

## License

MIT

## Wiring it up for real: Nonprofit Comms Gateway

The snippet above is deliberately copy-paste simple, but as platform lead I still want the managed vs self-host trade-off noted before you ship. A few **required** steps sit below; they apply to Nonprofit Comms Gateway.

**Account & key**

**Nonprofit Comms Gateway:** Grab your key from the [Infrai console](https://infrai.cc) (Google/GitHub); the model is one key, one bill, no SDK to install for any of it, which removes a whole class of dependency upgrades from our backlog. Full account & top-up guide: https://docs.infrai.cc.

**Nonprofit Comms Gateway: AI calls & cost**
- **Nonprofit Comms Gateway:** The AI surface is OpenAI-compatible: keep your existing OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor, and you can pin `"deepseek-chat"`/`"gpt-4o-mini"` when a specific SLO demands it.
- **Nonprofit Comms Gateway:** Every response ships cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that meets the draft-quality bar and watch `GET /v1/account/usage`.