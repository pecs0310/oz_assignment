"""kr_claims.xlsx -> dashboard 집계 JSON (data.json) 생성 스크립트."""
import json
import sys
import pandas as pd

XLSX = sys.argv[1] if len(sys.argv) > 1 else "kr_claims.xlsx"
OUT = sys.argv[2] if len(sys.argv) > 2 else "data.json"


def load(path):
    """모든 시트를 글자(str)로 읽는다: 031, 01 같은 앞자리 0 코드 보존."""
    return pd.read_excel(path, sheet_name=None, dtype=str)


def prep_claim(t):
    c = t["claim"].copy()
    for col in ["rvd_rpe_tamt_amt", "rvd_slf_brdn_amt", "rvd_insup_brdn_amt"]:
        c[col] = pd.to_numeric(c[col])
    c["month"] = c["recu_fr_dd"].str[:7]
    return c


def kpis(c):
    return {
        "claims": int(len(c)),
        "total_amt": int(c["rvd_rpe_tamt_amt"].sum()),
        "patients": int(c["jid"].nunique()),
        "avg_amt": int(round(c["rvd_rpe_tamt_amt"].mean())),
        "period": [c["recu_fr_dd"].min(), c["recu_fr_dd"].max()],
    }


def top_sick(c, sick, n=10):
    g = c.groupby("main_sick").agg(claims=("mid", "size"), amt=("rvd_rpe_tamt_amt", "sum")).reset_index()
    g = g.merge(sick[["sickcd", "krnm"]], left_on="main_sick", right_on="sickcd", how="left")
    g = g.sort_values("claims", ascending=False).head(n)
    return [{"code": r.main_sick, "name": r.krnm if isinstance(r.krnm, str) else r.main_sick,
             "claims": int(r.claims), "amt": int(r.amt)} for r in g.itertuples()]


def by_cl(c, inst, codes):
    names = codes[codes["code_type"] == "종별코드"].set_index("code")["code_nm"]
    m = c.merge(inst[["yid", "cl_cd"]], on="yid", how="left")
    g = m.groupby("cl_cd").agg(claims=("mid", "size"),
                               avg_amt=("rvd_rpe_tamt_amt", "mean"),
                               slf=("rvd_slf_brdn_amt", "sum"),
                               tot=("rvd_rpe_tamt_amt", "sum")).reset_index()
    g["name"] = g["cl_cd"].map(names)
    order = ["31", "21", "11", "01"]  # 의원 -> 병원 -> 종합병원 -> 상급종합병원
    g = g.set_index("cl_cd").loc[[o for o in order if o in g["cl_cd"].values]].reset_index()
    return [{"code": r.cl_cd, "name": r.name, "claims": int(r.claims),
             "avg_amt": int(round(r.avg_amt)), "slf_rate": round(r.slf / r.tot * 100, 1)}
            for r in g.itertuples()]


def monthly(c):
    c = c.assign(resp=c["main_sick"].str.startswith("J"))
    g = c.groupby("month").agg(total=("mid", "size"), resp=("resp", "sum")).reset_index()
    return [{"month": r.month, "total": int(r.total), "resp": int(r.resp)} for r in g.itertuples()]


def main():
    t = load(XLSX)
    c = prep_claim(t)
    data = {"kpi": kpis(c), "top_sick": top_sick(c, t["sick_master"]),
            "by_cl": by_cl(c, t["institution"], t["code_table"]), "monthly": monthly(c)}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(json.dumps(data, ensure_ascii=False)[:3000])


if __name__ == "__main__":
    main()
