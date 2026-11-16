import json,sys
rows=[json.loads(l) for l in open(sys.argv[1])]
tr=[r for r in rows if r["stage"]=="trimmed"]
w=tr[0]["weight"]
print("year real_output hired_hours")
for r in tr: print(r["year"], round(r["real_output"],1), round(r["hired_hours"]))
goods=sorted({g for r in tr for g in r["output"] if g in w})
# swing contribution per good: sum over consecutive years |delta weighted|
tot=0;contrib={}
for a,b in zip(tr,tr[1:]):
    for g in goods:
        d=w[g]*(b["output"].get(g,0)-a["output"].get(g,0)); contrib[g]=contrib.get(g,0)+abs(d)
tot=sum(contrib.values())
print("TOP GOODS share of sum|delta|, net signed changes by year")
for g in sorted(contrib,key=lambda g:-contrib[g])[:8]:
    print(g, round(contrib[g]/tot,3), [round(w[g]*b["output"].get(g,0)) for b in tr])
trades=sorted({t for r in tr for t in r["hired_by_trade"]})
c2={}
for a,b in zip(tr,tr[1:]):
    for t in trades: c2[t]=c2.get(t,0)+abs(b["hired_by_trade"].get(t,0)-a["hired_by_trade"].get(t,0))
t2=sum(c2.values())
print("TOP TRADES")
for t in sorted(c2,key=lambda t:-c2[t])[:8]:
    print(t, round(c2[t]/t2,3), [round(b["hired_by_trade"].get(t,0)) for b in tr])
