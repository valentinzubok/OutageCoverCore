# OutageCover — Studio Dev (chain 61997) deploy record

| | |
|---|---|
| **Network** | GenLayer Studio Dev / Studio Next — chain `61997` |
| **Contract** | [`0xF99E82326c4971d36dC71Bec29985c358939991B`](https://explorer-studio-dev.genlayer.com/address/0xF99E82326c4971d36dC71Bec29985c358939991B) |
| **Deploy tx** | [`0x160329ff…bddcc50`](https://explorer-studio-dev.genlayer.com/tx/0x160329ff6a53e1e482d03b1978c7e302950774dd7a7c8a44a308f7a77bddcc50) from `0x73064D61A55Fdc895a87fA0432637CdBfc80B7a3`, which has no role in the contract |
| **Source** | [`contracts/OutageCover.py`](contracts/OutageCover.py) — runner `py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng` |
| **Source sha256** | `3f79a14a4a8cee6fa6584282c77ed751be27d85ee762fed3d68391a4076c7ad3` |

## Verify the source yourself

```bash
curl -s -X POST https://studio-dev.genlayer.com/api -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"gen_getContractCode","params":["0xF99E82326c4971d36dC71Bec29985c358939991B"]}' \
  | python3 -c "import sys,json,base64,hashlib; print(hashlib.sha256(base64.b64decode(json.load(sys.stdin)['result'])).hexdigest())"
shasum -a 256 contracts/OutageCover.py
# both print 3f79a14a4a8cee6fa6584282c77ed751be27d85ee762fed3d68391a4076c7ad3
```

`scripts/verify_deployment.py` does the same in CI on every push.

## Lint

```bash
pip install genvm-linter
sh scripts/lint_current_sdk.sh
```

`genvm-lint lint` on the deployed file, then `check` and `typecheck` on a copy whose header and
imports are switched to the public runner `1jb45aa8…` (GenVM v0.3.0-rc7). Studio Dev accepts only
runner `5jycge4q…`, which is in no public GenVM release, so the linter cannot load its SDK; the
public runners are refused by Studio Dev with `invalid_contract runner malformed`. Result:
`Lint passed`, `Validation passed`, `No type errors found`. CI runs it on every push.

## The run

| Role | Address |
|---|---|
| underwriter | `0xa2c8395867a6cF6f1Bcd336f1F7F42DCD074F742` |
| Ann | `0xaC000D8FD2810C51Efa311b70df93B0Ae3BEaEBA` |
| Ben | `0xc453403210e982fbEfCcf6c504EBB698Fe89460a` |

Cover period of `api-1`: 2026-10-19 14:19:14 → 14:23:14 UTC. While it ran, the Harbor API status
page was updated by public commits: [`dab3ffb`](https://github.com/valentinzubok/OutageCover/commit/dab3ffb909866ca7c5499156b71be463b17e281e) reported a major outage and
[`9fe1384`](https://github.com/valentinzubok/OutageCover/commit/9fe138409647e9fa9cd2ca8d33a390c462028267) gave its start to the second, 14:19:46 UTC. Rule of `api-1`: *"Any
incident the page marks as a major outage of the API that starts inside the cover period."*

| # | Call | Sender | Result | What happened | Tx |
|---|------|--------|--------|---------------|----|
| 1 | `open_pool(api-1)` value 10 GEN | underwriter | SUCCESS | `api-1`: 10 GEN collateral, sales close in 150 s, cover 240 s, payout ×5, 2 agreeing rounds 60 s apart. Status page: `raw…/main/web/public/fixtures/status-api.html` | [`0x6e933df0…0d8802`](https://explorer-studio-dev.genlayer.com/tx/0x6e933df02edd38cfda684ba529496c405817b5f6e953bc592f752f0dc10d8802) |
| 2 | `open_pool(web-1)` value 4 GEN | underwriter | SUCCESS | `web-1`: 4 GEN collateral, same dates, payout ×4, 1 round. Status page pinned at commit `48da847`: lists only a major outage from 2026-09-12 | [`0xd2ff110a…f34fb5`](https://explorer-studio-dev.genlayer.com/tx/0xd2ff110a4e4305764a2c0ae0ea519c50d0c1c6e02980a1a78778afc0dff34fb5) |
| 3 | `buy_cover(api-1)` value 1 GEN | Ann | SUCCESS | 1 GEN premium → pays 5 GEN | [`0xfb28a244…a824e2`](https://explorer-studio-dev.genlayer.com/tx/0xfb28a2444054d0f035e7b28e5a53e523227961b045825114f3d0a4d20ca824e2) |
| 4 | `buy_cover(api-1)` value 1 GEN | Ben | SUCCESS | 1 GEN premium → pays 5 GEN | [`0x065932d1…dd136e`](https://explorer-studio-dev.genlayer.com/tx/0x065932d167e500b4260d8281f072e69b866a1c5fe2b9d3d7c98d9cf89cdd136e) |
| 5 | `buy_cover(web-1)` value 1 GEN | Cat | SUCCESS | `web-1`: 1 GEN premium → pays 4 GEN | [`0x47018728…65dc0e`](https://explorer-studio-dev.genlayer.com/tx/0x470187287ad6a96d8e25a485e4ec23363d1d6c9640a99d3048b190c26d65dc0e) |
| 6 | `buy_cover(api-1)` value 1 GEN | **underwriter** | SUCCESS | refused in the return value: `the underwriter cannot buy its own cover`; 1 GEN credited | [`0xf135b8bc…200544`](https://explorer-studio-dev.genlayer.com/tx/0xf135b8bce96c94dd49bef6d4874d4c1621588fadc5ea740a8a77589fa0200544) |
| 7 | `buy_cover(api-1)` value 2 GEN | **stranger** | SUCCESS | 2 GEN would need 10 GEN of payout but only 2 GEN of capacity is free: `the collateral cannot cover this policy`; credited | [`0xa82dcc29…5296af`](https://explorer-studio-dev.genlayer.com/tx/0xa82dcc29660774d889005ff92f8e8de07fbf601eb3d88d42c05aa6094a5296af) |
| 8 | `settle(api-1)` | stranger | **ERROR** | **UserError** `too early: the next round opens at …` — cover has not ended | [`0x4712d3d9…aba2b7`](https://explorer-studio-dev.genlayer.com/tx/0x4712d3d9fe6f3a01839911137ca76f0ddfb9cd8bd99d96354ae47739e6aba2b7) |
| 9 | `buy_cover(api-1)` value 1 GEN | **stranger** | SUCCESS | after sales closed: `sales are closed`; credited | [`0xbdbb893e…308968`](https://explorer-studio-dev.genlayer.com/tx/0xbdbb893eefbadf726e4073597d1411b0ca5eb3bbe5e664044c0c00fd74308968) |
| 10 | `settle(web-1)` | stranger | SUCCESS | FINALIZED. `web-1`: validators agree **no incident** in the cover period (the September outage is outside it) → **clean** | [`0x53aa21ab…8788f1`](https://explorer-studio-dev.genlayer.com/tx/0x53aa21abe828e36f96c8ac1cba65dcd30633dc93f60a900bc989cb200a8788f1) |
| 11 | `settle(api-1)` | stranger | SUCCESS | `api-1` round 1: validators agree **incident** → proposal 1 of 2 | [`0xf753d911…3aad9e`](https://explorer-studio-dev.genlayer.com/tx/0xf753d911ffeea0a4757f72f3adba93cf1c3dc4314554586ca3457787513aad9e) |
| 12 | `settle(api-1)` | stranger | SUCCESS | FINALIZED. `api-1` round 2: **incident** again → **triggered** | [`0xe122b636…9108a4`](https://explorer-studio-dev.genlayer.com/tx/0xe122b6361e25180a80b420cc72fc4f02d6e6efc10cfe832c6823650bc09108a4) |
| 13 | `claim(api-1)` | Ann | SUCCESS | FINALIZED. claim: 5 GEN | [`0xf55ee7c8…3f26eb`](https://explorer-studio-dev.genlayer.com/tx/0xf55ee7c881a5f4af4c0016ea2db49037c81fe3ff7dc141ec3a3f4c46833f26eb) |
| 14 | `claim(api-1)` | Ben | SUCCESS | FINALIZED. claim: 5 GEN | [`0x229b4f06…821a96`](https://explorer-studio-dev.genlayer.com/tx/0x229b4f06b2193d04cd9eb1e368417e941c7bb10f280da6475380d47d92821a96) |
| 15 | `claim(api-1)` | **Ann** | **ERROR** | **UserError** `already claimed` | [`0xbe2822dd…c0e297`](https://explorer-studio-dev.genlayer.com/tx/0xbe2822ddccf81a02c80f118ff17cf7f2b4c2b5be843c5592324b260147c0e297) |
| 16 | `claim(web-1)` | **Cat** | **ERROR** | **UserError** `nothing to claim: the pool is clean` | [`0xba11e427…7b7e30`](https://explorer-studio-dev.genlayer.com/tx/0xba11e4270b3ad931897957175747a8336c0969f375e367c41b6c6f922d7b7e30) |
| 17 | `withdraw_underwriter(api-1)` | **stranger** | **ERROR** | **UserError** `only the underwriter may withdraw` | [`0xb4a47c72…8e0af5`](https://explorer-studio-dev.genlayer.com/tx/0xb4a47c728201b9b1f62ad2b444e880d4b0a53246477aa9d67d0b2a9dd58e0af5) |
| 18 | `withdraw_underwriter(api-1)` | underwriter | SUCCESS | FINALIZED. `api-1`: what no policy can claim, 10 + 2 − 10 = 2 GEN | [`0xbc4770c5…864f5f`](https://explorer-studio-dev.genlayer.com/tx/0xbc4770c54be473489ec03de12244549a96399d142acc1a97f41ed94351864f5f) |
| 19 | `withdraw_underwriter(web-1)` | underwriter | SUCCESS | FINALIZED. `web-1`: collateral + premium, 5 GEN | [`0x8469f443…909a33`](https://explorer-studio-dev.genlayer.com/tx/0x8469f4435748216af1cf6af80902404768e848c05281e6856b510923ae909a33) |
| 20 | `withdraw_credit()` | underwriter | SUCCESS | FINALIZED. the refused 1 GEN | [`0xa746a376…7065d2`](https://explorer-studio-dev.genlayer.com/tx/0xa746a37682269e1bedc34aa4a9dcab07b03168a6033269b45ad266b7417065d2) |
| 21 | `withdraw_credit()` | stranger | SUCCESS | FINALIZED. the refused 3 GEN | [`0xa759369b…2934e1`](https://explorer-studio-dev.genlayer.com/tx/0xa759369be264be68f42ed6ea09132407ff0c70fae6cc9fd3d26426ef842934e1) |

End state, read from chain:

```
get_stats     {"pools":2,"by_status":{"triggered":1,"clean":1}}
get_balance   {"balance":"0","credits":"0","held":"0"}
api-1         triggered; rounds: incident (proposed) -> incident (confirmed), page sha-256 ced0daaa92ff…
web-1         clean;     rounds: no incident (proposed, final at 1 round), page sha-256 c1f6894a70ce…
Ann, Ben      98.9999 -> 103.9997 / 103.9998   (1 GEN premium, 5 GEN payout)
```
