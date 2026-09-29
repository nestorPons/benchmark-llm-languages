#!/usr/bin/env python3
"""Análisis v1: dataset, scoring, radar, Pareto, sensibilidad.

Lee results/raw/ (Eje A) y results/summary/load/ (Eje B), calcula agregados
(mediana, p25-p75, pass rate), normaliza 0-1, aplica pesos, y genera gráficos.

Uso:
    analyze.py [--out report]
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "results" / "raw"
LOAD = ROOT / "results" / "summary" / "load"

OBJECTIVES = [
    "reduce_output_tokens",
    "reduce_context_tokens",
    "reduce_generation_errors",
    "reduce_execution_time",
    "reduce_total_ai_cost",
]

OBJ_LABELS = {
    "reduce_output_tokens": "Tokens salida",
    "reduce_context_tokens": "Tokens contexto",
    "reduce_generation_errors": "Sin errores",
    "reduce_execution_time": "Rapidez ejec.",
    "reduce_total_ai_cost": "Coste IA bajo",
}

WEIGHTS_DEFAULT = {
    "reduce_output_tokens": 0.15,
    "reduce_context_tokens": 0.15,
    "reduce_generation_errors": 0.20,
    "reduce_execution_time": 0.30,
    "reduce_total_ai_cost": 0.20,
}

WEIGHTS_ALT = {
    "prod_heavy": {"reduce_output_tokens": 0.20, "reduce_context_tokens": 0.20,
                   "reduce_generation_errors": 0.25, "reduce_execution_time": 0.15,
                   "reduce_total_ai_cost": 0.20},
    "perf_heavy": {"reduce_output_tokens": 0.05, "reduce_context_tokens": 0.05,
                   "reduce_generation_errors": 0.10, "reduce_execution_time": 0.60,
                   "reduce_total_ai_cost": 0.20},
}


def _median(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def _p25(xs):
    xs = sorted(x for x in xs if x is not None)
    return xs[len(xs) // 4] if xs else None


def _p75(xs):
    xs = sorted(x for x in xs if x is not None)
    return xs[(3 * len(xs)) // 4] if xs else None


def load_eje_a():
    rows = []
    for p in glob.glob(str(RAW / "*" / "*" / "*" / "rep*.json")):
        try:
            d = json.load(open(p))
        except (OSError, json.JSONDecodeError):
            continue
        rows.append(d)
    return rows


def load_eje_b():
    out = {}
    for p in glob.glob(str(LOAD / "*" / "*" / "*" / "summary.json")):
        try:
            d = json.load(open(p))
        except (OSError, json.JSONDecodeError):
            continue
        key = (d.get("task"), d.get("language"))
        out[key] = d.get("runs", [])
    return out


def aggregate_eje_a(rows):
    from collections import defaultdict
    groups = defaultdict(list)
    for r in rows:
        groups[(r["model"], r["task"], r["language"])].append(r)
    agg = {}
    for key, rs in groups.items():
        n = len(rs)
        passed = sum(1 for r in rs if r["passed"])
        agg[key] = {
            "n": n,
            "pass_rate": passed / n if n else 0,
            "pass_at_1_rate": sum(1 for r in rs if r.get("pass_at_1")) / n if n else 0,
            "iters_med": _median([r["iterations"] for r in rs]),
            "in_med": _median([r["input_tokens_total"] for r in rs]),
            "out_med": _median([r["output_tokens_total"] for r in rs]),
            "cost_med": _median([r["cost_usd"] for r in rs]),
            "cost_p25": _p25([r["cost_usd"] for r in rs]),
            "cost_p75": _p75([r["cost_usd"] for r in rs]),
        }
    return agg


def aggregate_eje_b(load):
    agg = {}
    for (task, lang), runs in load.items():
        by_vus = {}
        for r in runs:
            if r.get("error"):
                continue
            by_vus.setdefault(r["vus"], []).append(r)
        agg[(task, lang)] = {
            vus: {
                "tput_med": _median([x["http_reqs"] for x in rs]),
                "p95_med": _median([x["http_req_duration_p95"] for x in rs]),
                "p99_med": _median([x["http_req_duration_p99"] for x in rs]),
                "n": len(rs),
            }
            for vus, rs in by_vus.items()
        }
    return agg


def _norm_higher(values):
    vals = [v for v in values if v is not None]
    if not vals or max(vals) == min(vals):
        return [1.0 if v is not None else 0.0 for v in values]
    lo, hi = min(vals), max(vals)
    return [(v - lo) / (hi - lo) if v is not None else 0.0 for v in values]


def _norm_lower(values):
    vals = [v for v in values if v is not None]
    if not vals or max(vals) == min(vals):
        return [1.0 if v is not None else 0.0 for v in values]
    lo, hi = min(vals), max(vals)
    return [(hi - v) / (hi - lo) if v is not None else 0.0 for v in values]


def score(agg_a, agg_b, weights):
    keys = sorted(agg_a.keys())
    outs = [agg_a[k]["out_med"] for k in keys]
    ins = [agg_a[k]["in_med"] for k in keys]
    passr = [agg_a[k]["pass_rate"] for k in keys]
    costs = [agg_a[k]["cost_med"] for k in keys]
    tputs = []
    for (model, task, lang) in keys:
        b = (agg_b.get((task, lang), {}) or {}).get(10) or (agg_b.get((task, lang), {}) or {}).get(1) or {}
        tputs.append(b.get("tput_med"))
    s_out = _norm_lower(outs)
    s_in = _norm_lower(ins)
    s_pass = _norm_higher(passr)
    s_tput = _norm_higher(tputs)
    s_cost = _norm_lower(costs)
    scores = {}
    for i, k in enumerate(keys):
        obj = {
            "reduce_output_tokens": s_out[i],
            "reduce_context_tokens": s_in[i],
            "reduce_generation_errors": s_pass[i],
            "reduce_execution_time": s_tput[i],
            "reduce_total_ai_cost": s_cost[i],
        }
        total = sum(obj[o] * weights[o] for o in OBJECTIVES)
        scores[k] = {"objectives": obj, "total": total}
    return scores


def write_dataset(agg_a, agg_b, out_dir, scores=None):
    out_dir.mkdir(parents=True, exist_ok=True)
    if scores is None:
        scores = score(agg_a, agg_b, WEIGHTS_DEFAULT)
    order = sorted(agg_a.keys(), key=lambda k: -scores.get(k, {}).get("total", 0))
    with open(out_dir / "dataset.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["model", "task", "language", "n", "pass_rate", "pass_at_1",
                    "iters_med", "in_med", "out_med", "cost_med", "cost_p25", "cost_p75",
                    "tput_vus10_med", "p95_vus10_med", "score_total"])
        for (model, task, lang) in order:
            a = agg_a[(model, task, lang)]
            b = (agg_b.get((task, lang), {}) or {}).get(10, {})
            tot = scores.get((model, task, lang), {}).get("total")
            w.writerow([model, task, lang, a["n"], f"{a['pass_rate']:.2f}",
                        f"{a['pass_at_1_rate']:.2f}", a["iters_med"], a["in_med"],
                        a["out_med"], f"{a['cost_med']:.4f}" if a["cost_med"] is not None else "",
                        f"{a['cost_p25']:.4f}" if a["cost_p25"] is not None else "",
                        f"{a['cost_p75']:.4f}" if a["cost_p75"] is not None else "",
                        f"{b.get('tput_med'):.0f}" if b.get("tput_med") else "",
                        f"{b.get('p95_med'):.1f}" if b.get("p95_med") else "",
                        f"{tot:.3f}" if tot is not None else ""])
    with open(out_dir / "scores.json", "w") as fh:
        json.dump({"default": {f"{m}|{t}|{l}": s for (m, t, l), s in
                               scores.items()}}, fh, indent=2)


def plot_radar(scores, out_dir):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import math
    except ImportError:
        return []
    paths = []
    combos = sorted(scores.keys())
    n = len(combos)
    cols = 3
    rows = math.ceil(n / cols) if n else 1
    fig, axes = plt.subplots(rows, cols, subplot_kw={"projection": "polar"},
                             figsize=(4 * cols, 4 * rows))
    if n == 1:
        axes = [[axes]]
    elif rows == 1:
        axes = [axes]
    angles = [i / len(OBJECTIVES) * 2 * math.pi for i in range(len(OBJECTIVES))]
    angles += angles[:1]
    for ax, key in zip([a for row in axes for a in row], combos):
        vals = [scores[key]["objectives"][o] for o in OBJECTIVES]
        vals += vals[:1]
        ax.plot(angles, vals, "o-")
        ax.fill(angles, vals, alpha=0.25)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([OBJ_LABELS[o] for o in OBJECTIVES], fontsize=8)
        ax.set_ylim(0, 1)
        ax.set_title(f"{key[0][:12]} {key[1][:10]} {key[2]}", fontsize=9)
    for ax in [a for row in axes for a in row][len(combos):]:
        ax.axis("off")
    fig.tight_layout()
    p = out_dir / "radar.png"
    fig.savefig(p, dpi=100)
    paths.append(str(p))
    return paths


def plot_pareto(agg_a, agg_b, out_dir):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return []
    pts = []
    for (model, task, lang), a in agg_a.items():
        if a["cost_med"] is None:
            continue
        b = (agg_b.get((task, lang), {}) or {}).get(10) or {}
        tput = b.get("tput_med")
        if not tput:
            continue
        pts.append((f"{lang} ({model[:8]})", a["cost_med"], tput))
    if not pts:
        return []
    fig, ax = plt.subplots(figsize=(7, 5))
    for label, cost, tput in pts:
        ax.scatter(cost, tput)
        ax.annotate(label, (cost, tput), fontsize=8)
    ax.set_xlabel("Coste mediano IA (USD, log)")
    ax.set_ylabel("Throughput mediano (req/s, VUS=10)")
    ax.set_xscale("log")
    ax.set_title("Pareto: coste IA vs rendimiento")
    fig.tight_layout()
    p = out_dir / "pareto.png"
    fig.savefig(p, dpi=100)
    return [str(p)]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(ROOT / "report"))
    args = ap.parse_args(argv)
    out = Path(args.out)

    rows = load_eje_a()
    load = load_eje_b()
    agg_a = aggregate_eje_a(rows)
    agg_b = aggregate_eje_b(load)

    scores_def = score(agg_a, agg_b, WEIGHTS_DEFAULT)
    sens = {"default": {f"{m}|{t}|{l}": round(s["total"], 3) for (m, t, l), s in scores_def.items()}}
    for name, w in WEIGHTS_ALT.items():
        s = score(agg_a, agg_b, w)
        sens[name] = {f"{m}|{t}|{l}": round(v["total"], 3) for (m, t, l), v in s.items()}

    write_dataset(agg_a, agg_b, out)
    with open(out / "sensitivity.json", "w") as fh:
        json.dump(sens, fh, indent=2)
    radar = plot_radar(scores_def, out)
    pareto = plot_pareto(agg_a, agg_b, out)

    print(f"Eje A combos: {len(agg_a)}, Eje B series: {len(agg_b)}")
    print("Ranking (default):")
    for (m, t, l), s in sorted(scores_def.items(), key=lambda kv: -kv[1]["total"]):
        print(f"  {s['total']:.2f}  {m} {t} {l}")
    print(f"Wrote dataset.csv, scores.json, sensitivity.json, {radar}, {pareto} in {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
