# OutageCoverCore

<p align="center">
  <strong>Outage insurance that pays when validators agree the provider's own status page reported the incident.</strong>
</p>

<p align="center">
  <a href="https://github.com/valentinzubok/OutageCoverCore/actions/workflows/ci.yml"><img src="https://github.com/valentinzubok/OutageCoverCore/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <img src="https://img.shields.io/badge/GenLayer-Studio%20Dev%2061997-f87171?style=flat-square" alt="Studio Dev" />
</p>

This repository holds the intelligent contract, its tests, its lint script and its deploy record,
and nothing else. The console that uses it is a separate project: [OutageCover](https://github.com/valentinzubok/OutageCover).

---

## The trust problem

Parametric insurance is supposed to pay on a fact instead of a claims adjuster. The weak spot is
who reports the fact. A price oracle cannot read "API major outage, 47 minutes" off a status page,
and an insurer that decides for itself whether the outage counted is a claims adjuster again.

**OutageCover makes "did the provider's own status page report a qualifying incident inside the
cover period?" a consensus question**, and lets the answer move the money. Everything that
decides it is fixed when the pool opens.

```
open_pool(pool_id, service, status_url, incident_rule, sales_close_in, cover_length,
          multiple, settle_interval, rounds_required)                     PAYABLE
      the underwriter escrows collateral. The status page, the rule, the dates, the payout
      multiple and the settlement schedule are fixed here. No setters, no owner.

buy_cover(pool_id)                                                        PAYABLE
      the attached value is the premium; the policy pays premium x multiple.
      one policy per address, never the underwriter, only while sales are open - sales close
      before cover starts, so nobody buys after an outage began. A policy the collateral
      cannot cover is refused and credited back.

settle(pool_id)                     anyone, after cover ends; takes a pool id and nothing else
      refused before a full settle_interval since the previous accepted round
      validators freeze the status page (strict_eq) and agree on one boolean:
      a qualifying incident that overlaps the cover period?
        same answer as the standing proposal -> one more confirmation
        a different answer                   -> the count starts again from 1
        page unreachable                     -> nothing is proposed or overturned
      rounds_required agreeing rounds -> TRIGGERED (incident) or CLEAN (none)

claim(pool_id)                      a policyholder: premium x multiple on TRIGGERED,
                                    the premium back on VOID
withdraw_underwriter(pool_id)       the underwriter, once final: what no policy can claim
expire(pool_id)                     anyone, after the settlement deadline: VOID
withdraw_credit()                   take back what a payable call refused to escrow
```

### Why it fails the way it does

| Risk | What stops it |
|---|---|
| The insurer decides the outage "did not count" | Nobody decides. `settle` takes a pool id only; the answer is what validators agree on, against the rule fixed at `open_pool`. There is no owner or admin. |
| Buying cover after the outage has started | Sales close before cover starts; `buy_cover` after that is refused (and credited). |
| An incident outside the cover period | The prompt states the cover period in UTC and counts only incidents that overlap it. On chain, the web pool's status page listed a major outage from September: validators agreed it did not count. |
| One wrong reading pays or denies | `rounds_required` agreeing rounds, each a full interval apart, elapsed time not a calendar window. A different answer restarts the count; an unreachable page changes nothing. |
| The pool promising more than it holds | Every policy reserves premium x multiple; a purchase that would exceed collateral + premiums is refused. The underwriter's share is computed after every payout is reserved. |
| The status page steering the model | Service, rule and page excerpts are fenced as untrusted data, inner fences neutralized, instruction-like phrasing flagged and stored. |
| `"true"`, `1` or `"yes"` counted as a verdict | `literal_bool()` accepts only JSON `true`/`false`. Anything else reverts. |
| A refused call stranding money | Value attached to a reverting call is not returned on this network, so both payable methods never raise once value is attached; the amount is credited. |
| A pool nobody settles | `expire` voids it after the committed deadline: buyers get premiums back, the underwriter the collateral. |
| A payout that pays nobody | External wallet transfers, after the books are updated. The contract balance equals what pools still hold plus credits after every step of a random run. |

## Live

| | |
|---|---|
| Network | GenLayer Studio Dev / Studio Next — chain `61997` |
| Contract | [`0xF99E82326c4971d36dC71Bec29985c358939991B`](https://explorer-studio-dev.genlayer.com/address/0xF99E82326c4971d36dC71Bec29985c358939991B) |
| Deploy record | [`STUDIO_DEV_DEPLOY.md`](STUDIO_DEV_DEPLOY.md) — every transaction of the demo, including the refused ones |

## Lint

`sh scripts/lint_current_sdk.sh` runs the official GenVM linter (`genvm-lint lint`, `check` and
`typecheck`) and CI runs it on every push. Every refusal raises `gl.vm.UserError`; every method of
the contract class takes `self`. See [`STUDIO_DEV_DEPLOY.md`](STUDIO_DEV_DEPLOY.md#lint).

## Demo pages

Copies of the pages the on-chain demo read are in [`fixtures/`](fixtures/).

Files in this repository: [`status-api.html`](fixtures/status-api.html) reported a major
outage during the demo's cover period (added by a public commit while cover was running), and
[`status-web.html`](fixtures/status-web.html) lists only an older incident.

## Tests

```bash
pip install -r requirements-dev.txt
python3 -m pytest -q      # 53 tests
```

[`tests/test_outagecover.py`](tests/test_outagecover.py): an agreed incident pays every holder and
leaves the underwriter the rest; a clean period returns everything to the underwriter; a different
answer restarts the count; an unreachable page changes nothing; no cover after sales close, one
policy per address, never the underwriter, collateral must cover every payout; no settlement
before cover ends or inside the interval, across midnight and under hammering; ten malformed
answers, a model error and a consensus failure revert; fencing and flagged injection; voiding;
ten refused pools credit everything; pools do not share money; the books balance through a
300-step random run.

## License

[MIT](LICENSE) © 2026 Valentyn Zubok
