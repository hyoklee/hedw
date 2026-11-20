#!/usr/bin/env python3
"""Ask the hedw/solar-coherence agent questions (clio-agent 0.9.7.x SDK).

Start the server first (agent/clio-agent/start.sh), then, with the 0.9.7 venv:

    ~/.local/share/clio/clio-agent-097/.venv/bin/python agent/clio-agent/ask.py \
        "Which cities are anomalous in the latest run, and why?" --out answer.json

    ask.py --bench --out agent/results/llm/bench_<stamp>   # fixed questions, numbers checked

Each question runs on a new session pinned to the agent. Only tools whose name
starts with an --allow prefix are approved (default hedw_; shell is denied
unless --allow-shell). The JSON log holds tool calls, permissions, answer,
tokens and timings. In --bench mode every number the answer must contain is
taken from the run's own files and checked in the answer text.
"""
import argparse, csv, json, os, re, sys, time
from pathlib import Path

from clio_agent.client import ClioClient
from clio_agent.client.events import MessageCompleted, PermissionRequested, ToolCallCompleted

AGENT = "hedw/solar-coherence"
ROOT = Path(__file__).resolve().parents[2]


def answer_of(msg):
    parts = msg.parts or []
    texts = [p.text for p in parts if getattr(p, "type", "") == "text" and getattr(p, "text", "")]
    ans = [p.text for p in parts if getattr(p, "type", "") == "text" and getattr(p, "text", "")
           and ((getattr(p, "metadata", None) or {}).get("signature_field_name") == "answer")]
    return "\n".join(ans or texts[-1:]).strip()


def ask(c, question, agent=AGENT, timeout=600, allow=("hedw_",)):
    log = dict(question=question, agent=agent, tools=[], permissions=[])
    t0 = time.time()
    s = c.sessions.create(title=f"hedw: {question[:40]}", metadata={"agent_ref": agent})
    log["session_id"] = s.id
    c.messages.post(s.id, question)
    with c.sessions.events(s.id, reconnect_attempts=3) as stream:
        for ev in stream:
            if time.time() - t0 > timeout:
                log["status"] = "timeout"; break
            if isinstance(ev, PermissionRequested):
                name = ev.permission.tool_call.tool_name or ""
                decision = "allow" if name.startswith(tuple(allow)) else "deny"
                c.permissions.respond(ev.permission.id, decision)
                log["permissions"].append(dict(tool=name, decision=decision))
            elif isinstance(ev, ToolCallCompleted):
                log["tools"].append(dict(tool=ev.tool, ok=ev.ok))
            elif isinstance(ev, MessageCompleted):
                log["stop_reason"] = ev.stop_reason
                if ev.error_info:
                    log["error"] = str(ev.error_info)
                log.setdefault("status", "completed"); break
    log["elapsed_s"] = round(time.time() - t0, 1)
    msgs = [m for m in c.messages.list(s.id) if getattr(m, "role", "") == "assistant"]
    log["answer"] = answer_of(msgs[-1]) if msgs else ""
    try:
        sess = c.sessions.get(s.id)
        log["tokens_input"], log["tokens_output"] = sess.tokens_input, sess.tokens_output
    except Exception:  # noqa: BLE001
        pass
    return log


def latest_run():
    runs = sorted(p for p in (ROOT / "agent/results").glob("run_*") if (p / "summary.json").is_file())
    return runs[-1]


def fmt_variants(x):
    """Ways a number may legitimately be written in an answer."""
    x = float(x)
    out = {f"{x:.4f}", f"{x:.3f}", f"{x:.2f}", f"{x:.1f}"}
    if x == int(x):
        out.add(str(int(x)))
    return {v.rstrip("0").rstrip(".") if "." in v else v for v in out} | out


def bench_tasks(run):
    s = json.load(open(run / "summary.json"))
    cities = {r["city"]: r for r in csv.DictReader(open(run / "cities.csv"))}
    t = [("How many cities were analysed in the latest solar-coherence run, and how many were flagged anomalous?",
          [s["cities_analysed"], s["n_anomalous_cities"]]),
         ("What is the median daily correlation (r_daily) between NSRDB GHI and NASA POWER across cities in the latest run?",
          [s["distribution_all_cities"]["r_daily"]["median"]]),
         ("Which city has the lowest daily correlation in the latest run, and what is its value?",
          [s["lowest_r_daily"][0]["city"], s["lowest_r_daily"][0]["r_daily"]])]
    for name in ["Texas_Dallas", s["lowest_r_daily"][0]["city"]]:
        r = cities[name]
        t.append((f"For {name} in the latest run, give r_daily, bias_pct and the number of anomalous days.",
                  [r["r_daily"], r["bias_pct"], r["anomalous_days"]]))
    return t


def score(answer, expect):
    a = answer.replace(",", "")
    hits = []
    for e in expect:
        if isinstance(e, str) and not re.fullmatch(r"-?[\d.]+", e):
            hits.append(e.lower() in answer.lower() or e.split("_")[-1].lower() in answer.lower())
        else:
            hits.append(any(re.search(rf"(?<![\d.]){re.escape(v)}(?![\d])", a) for v in fmt_variants(e)))
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question", nargs="?")
    ap.add_argument("--url", default="http://127.0.0.1:8100")
    ap.add_argument("--agent", default=AGENT)
    ap.add_argument("--allow-shell", action="store_true")
    ap.add_argument("--bench", action="store_true")
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--out")
    a = ap.parse_args()
    allow = ("hedw_",) + (("shell",) if a.allow_shell else ())
    c = ClioClient(base_url=a.url)
    if not a.bench:
        log = ask(c, a.question, a.agent, a.timeout, allow)
        print(log["answer"])
        print(f"[{log.get('status')} {log['elapsed_s']} s, tools {[x['tool'] for x in log['tools']]}, "
              f"tokens in/out {log.get('tokens_input')}/{log.get('tokens_output')}]", file=sys.stderr)
        if a.out:
            json.dump(log, open(a.out, "w"), indent=1)
        return
    run = latest_run()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    rows = []
    for rep in range(a.reps):
        for i, (q, exp) in enumerate(bench_tasks(run)):
            log = ask(c, q, a.agent, a.timeout, allow)
            hits = score(log["answer"], exp)
            log.update(run=run.name, expect=[str(e) for e in exp], hits=hits, correct=all(hits))
            json.dump(log, open(out / f"q{i}_r{rep}.json", "w"), indent=1)
            rows.append(dict(q=i, rep=rep, correct=all(hits), hits=sum(hits), n=len(hits),
                             elapsed_s=log["elapsed_s"], tools=len(log["tools"]),
                             tokens_in=log.get("tokens_input"), status=log.get("status")))
            print(rows[-1], flush=True)
    json.dump(dict(run=run.name, agent=a.agent, rows=rows,
                   correct=sum(r["correct"] for r in rows), total=len(rows)), open(out / "bench.json", "w"), indent=1)
    print(f"{sum(r['correct'] for r in rows)}/{len(rows)} correct")


if __name__ == "__main__":
    main()
