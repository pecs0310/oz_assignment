"""kr_claims.xlsx -> 대시보드 집계 JSON (data.json) 생성 스크립트.

독자: 상급종합병원 영상의학과장.
"""
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



# 영상검사 수요가 큰 질환군 (KCD 코드 앞자리 기준, 본 대시보드의 가정)
IMG_GROUPS = ["뇌혈관질환", "악성신생물", "손상", "폐렴", "근골격계"]


def img_group(code):
    """주상병 코드 -> 질환군. CT/MRI 등 영상검사가 진단·추적에 핵심인 질환군만 따로 묶는다."""
    a, n = code[0], code[1:3]
    if a == "I" and "60" <= n <= "69":
        return "뇌혈관질환"
    if a == "C":
        return "악성신생물"
    if a == "S":
        return "손상"
    if a == "J" and "12" <= n <= "18":
        return "폐렴"
    if a == "M":
        return "근골격계"
    return "기타"


def tertiary(c, inst):
    """상급종합병원(cl_cd 01) 명세서만 남기고 질환군을 붙인다."""
    m = c.merge(inst[["yid", "cl_cd"]], on="yid", how="left")
    s = m[m["cl_cd"] == "01"].copy()
    s["grp"] = s["main_sick"].map(img_group)
    return s


def tertiary_kpis(s):
    img = s[s["grp"] != "기타"]
    return {
        "claims": int(len(s)),
        "total_amt": int(s["rvd_rpe_tamt_amt"].sum()),
        "img_claim_pct": round(len(img) / len(s) * 100, 1),
        "img_amt_pct": round(img["rvd_rpe_tamt_amt"].sum() / s["rvd_rpe_tamt_amt"].sum() * 100, 1),
    }


def group_share(s):
    """질환군별 명세서 비중(%)과 진료비 비중(%)."""
    g = s.groupby("grp").agg(claims=("mid", "size"), amt=("rvd_rpe_tamt_amt", "sum"),
                             inpatient=("fom_tp_cd", lambda x: int((x == "021").sum())))
    g = g.reindex(IMG_GROUPS + ["기타"]).fillna(0)
    return [{"name": k, "claims": int(r.claims), "inpatient": int(r.inpatient),
             "claim_pct": round(r.claims / g.claims.sum() * 100, 1),
             "amt_pct": round(r.amt / g.amt.sum() * 100, 1),
             "avg_amt": int(round(r.amt / r.claims)) if r.claims else 0}
            for k, r in g.iterrows()]


def top_sick_amt(s, sick, n=10):
    """상급종합병원 진료비 합계 Top N 상병."""
    g = s.groupby("main_sick").agg(claims=("mid", "size"), amt=("rvd_rpe_tamt_amt", "sum"),
                                   patients=("jid", "nunique")).reset_index()
    g = g.merge(sick[["sickcd", "krnm"]], left_on="main_sick", right_on="sickcd", how="left")
    g = g.sort_values("amt", ascending=False).head(n)
    return [{"code": r.main_sick, "name": r.krnm, "grp": img_group(r.main_sick),
             "claims": int(r.claims), "patients": int(r.patients), "amt": int(r.amt)}
            for r in g.itertuples()]


def main():
    t = load(XLSX)
    c = prep_claim(t)
    s = tertiary(c, t["institution"])
    data = {"kpi": kpis(c), "by_cl": by_cl(c, t["institution"], t["code_table"]),
            "t_kpi": tertiary_kpis(s), "groups": group_share(s),
            "t_top": top_sick_amt(s, t["sick_master"])}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(json.dumps(data, ensure_ascii=False)[:3000])


if __name__ == "__main__":
    main()
