"""Fetch the latest CFTC COT numbers for Gold and write cot.json.
Runs inside GitHub Actions (free). The MT5 EA reads cot.json from raw.githubusercontent.com."""
import datetime
import json
import sys
import urllib.parse
import urllib.request

DATASET = "6dca-aqww"   # CFTC "Legacy - Futures Only"
CODE = "088691"         # Gold (COMEX)
FIELDS = [
    "report_date_as_yyyy_mm_dd",
    "noncomm_positions_long_all", "noncomm_positions_short_all",
    "comm_positions_long_all", "comm_positions_short_all",
    "nonrept_positions_long_all", "nonrept_positions_short_all",
]


def fetch():
    query = {
        "cftc_contract_market_code": CODE,
        "$select": ",".join(FIELDS),
        "$order": "report_date_as_yyyy_mm_dd DESC",
        "$limit": "2",
    }
    url = "https://publicreporting.cftc.gov/resource/%s.json?%s" % (
        DATASET, urllib.parse.urlencode(query, quote_via=urllib.parse.quote))
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def build(rows):
    def num(row, key):
        return int(float(row[key]))

    cur = rows[0]
    out = {
        "date": cur["report_date_as_yyyy_mm_dd"][:10],
        "ncl": num(cur, "noncomm_positions_long_all"),
        "ncs": num(cur, "noncomm_positions_short_all"),
        "ccl": num(cur, "comm_positions_long_all"),
        "ccs": num(cur, "comm_positions_short_all"),
        "nrl": num(cur, "nonrept_positions_long_all"),
        "nrs": num(cur, "nonrept_positions_short_all"),
    }
    if len(rows) > 1:
        out["pncl"] = num(rows[1], "noncomm_positions_long_all")
        out["pncs"] = num(rows[1], "noncomm_positions_short_all")
    return out


def main():
    try:
        rows = fetch()
        if not rows:
            raise ValueError("CFTC returned no rows")
        data = build(rows)
    except Exception as exc:  # shows up in the Actions log
        print("COT update failed:", repr(exc))
        sys.exit(1)
    with open("cot.json", "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1)
    print("Wrote cot.json:", data, "at", datetime.datetime.now(datetime.timezone.utc).isoformat())


if __name__ == "__main__":
    main()
