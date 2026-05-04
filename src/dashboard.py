from __future__ import annotations

import json
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import pandas as pd
import plotly.express as px

from src.backtest import evaluate_models
from src.database import CrashDatabase
from src.stats import compute_stats


def create_app(db_path: str, threshold: float = 2.0) -> FastAPI:
    app = FastAPI(title="Crash Dashboard")

    @app.get("/api/overview")
    def overview() -> dict:
        db = CrashDatabase(db_path)
        df = db.to_dataframe()
        db.close()
        if df.empty:
            return {}
        st = compute_stats(df, threshold=threshold)
        bt = evaluate_models(df, threshold=threshold)
        return {"stats": st, "backtest": bt}

    @app.get("/api/charts")
    def charts() -> dict:
        db = CrashDatabase(db_path)
        df = db.to_dataframe()
        db.close()
        if df.empty:
            return {}
        df = df.sort_values("timestamp_utc")
        fig1 = px.line(df, x="timestamp_utc", y="crash_multiplier", title="Multiplier over time")
        fig2 = px.histogram(df, x="crash_multiplier", nbins=50, title="Histogram")
        ts = df.set_index("timestamp_utc")["crash_multiplier"]
        rolling = ts.rolling("1h").mean().reset_index(name="r1h")
        fig3 = px.line(rolling, x="timestamp_utc", y="r1h", title="Rolling 1h")
        return {"time": fig1.to_json(), "hist": fig2.to_json(), "roll": fig3.to_json()}

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return """
<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'>
<script src='https://cdn.plot.ly/plotly-2.35.2.min.js'></script>
<style>
body{background:#0f1117;color:#e8e8e8;font-family:Inter,Arial;margin:0} .wrap{padding:20px} .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
.card{background:rgba(255,255,255,.08);border-radius:14px;padding:14px;box-shadow:0 8px 24px rgba(0,0,0,.25)} h1{margin-top:0}
.tabs button{margin-right:8px;padding:8px 12px;border-radius:8px;border:0;background:#1f2430;color:#fff}
.section{margin-top:16px}
</style></head><body><div class='wrap'>
<h1>Crash Research Dashboard</h1><div class='tabs'><button onclick='show("overview")'>Overview</button><button onclick='show("live")'>Live Data</button><button onclick='show("graphs")'>Graphs</button><button onclick='show("backtest")'>Backtest Results</button><button onclick='show("settings")'>Settings</button></div>
<div id='overview' class='section'><div id='cards' class='grid'></div></div>
<div id='live' class='section' style='display:none'><div class='card'>Live updates every 10s from local DB.</div></div>
<div id='graphs' class='section' style='display:none'><div id='g1' class='card'></div><div id='g2' class='card'></div><div id='g3' class='card'></div></div>
<div id='backtest' class='section' style='display:none'><pre id='bt' class='card'></pre></div>
<div id='settings' class='section' style='display:none'><div class='card'>Configure endpoint/settings in config.yaml</div></div>
</div>
<script>
function show(id){['overview','live','graphs','backtest','settings'].forEach(x=>document.getElementById(x).style.display=x===id?'block':'none')}
async function load(){
 const o=await (await fetch('/api/overview')).json(); const c=document.getElementById('cards'); c.innerHTML='';
 if(o.stats){const rows=[['total rounds',o.stats.total_rounds],['latest crash multiplier',o.stats.max],['average multiplier',o.stats.average],['median multiplier',o.stats.median],['1h average',o.stats.rolling_avg_1h],['10h average',o.stats.rolling_avg_10h],['100h average',o.stats.rolling_avg_100h],['longest streak below 2x',o.stats.longest_streak_below_2],['model accuracy',o.backtest?.conclusion?.best_accuracy],['baseline accuracy',o.backtest?.baseline_majority?.accuracy]]; rows.forEach(r=>{c.innerHTML+=`<div class='card'><b>${r[0]}</b><div>${r[1]}</div></div>`})}
 document.getElementById('bt').textContent=JSON.stringify(o.backtest||{},null,2);
 const ch=await (await fetch('/api/charts')).json(); if(ch.time){Plotly.newPlot('g1', JSON.parse(ch.time).data, JSON.parse(ch.time).layout);Plotly.newPlot('g2', JSON.parse(ch.hist).data, JSON.parse(ch.hist).layout);Plotly.newPlot('g3', JSON.parse(ch.roll).data, JSON.parse(ch.roll).layout)}
}
setInterval(load,10000);load();
</script></body></html>"""

    return app
