from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import streamlit as st

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "site" / "data"
LANGUAGES = {"한국어": "ko", "English": "en", "中文": "zh", "Tiếng Việt": "vi"}
LANGUAGE_NAMES = {"ko": "쉬운 한국어", "en": "plain English", "zh": "简体中文", "vi": "tiếng Việt dễ hiểu"}
DOCUMENTS = {"급여명세서": "급여명세서", "임대차계약서": "임대차계약서", "공과금고지서": "공과금 고지서"}

UI = {
    "ko": {"tag": "대구 외국인을 위한 AI 금융생활 가이드", "headline": "복잡한 금융 문서,<br>사진 한 장으로 쉽게", "lead": "금액과 날짜, 주의할 조건을 찾아 선택한 언어로 설명해 드립니다.", "upload": "문서를 올려주세요", "sample": "샘플로 체험하기", "analyze": "AI로 문서 분석", "result": "핵심 내용을 정리했어요", "attention": "확인이 필요한 항목", "found": "문서에서 찾은 정보", "actions": "다음 행동", "unclear": "불명확하거나 확인이 필요한 내용", "support": "도움을 받을 수 있는 기관", "calendar": "금융 캘린더", "phishing": "피싱 체크", "consult": "상담카드", "ask": "AI에게 질문"},
    "en": {"tag": "AI financial guide for foreign residents in Daegu", "headline": "Understand financial documents<br>from a single photo", "lead": "We find amounts, dates and important conditions, then explain them in your language.", "upload": "Upload a document", "sample": "Try a sample", "analyze": "Analyze with AI", "result": "Here are the key details", "attention": "Needs your attention", "found": "Information found", "actions": "Next actions", "unclear": "Missing or unclear information", "support": "Support organizations", "calendar": "Financial calendar", "phishing": "Phishing check", "consult": "Consultation card", "ask": "Ask AI"},
    "zh": {"tag": "面向大邱外国居民的AI金融生活指南", "headline": "复杂的金融文件，<br>一张照片轻松看懂", "lead": "自动查找金额、日期和注意事项，并用您选择的语言说明。", "upload": "上传文件", "sample": "体验示例", "analyze": "AI分析文件", "result": "核心内容", "attention": "需要确认的项目", "found": "文件中的信息", "actions": "下一步行动", "unclear": "不清楚或需要确认的内容", "support": "可获得帮助的机构", "calendar": "金融日历", "phishing": "诈骗检测", "consult": "咨询卡", "ask": "向AI提问"},
    "vi": {"tag": "Trợ lý tài chính AI cho người nước ngoài tại Daegu", "headline": "Hiểu tài liệu tài chính<br>chỉ với một bức ảnh", "lead": "Tìm số tiền, ngày tháng và điều khoản quan trọng rồi giải thích bằng ngôn ngữ của bạn.", "upload": "Tải tài liệu lên", "sample": "Thử tài liệu mẫu", "analyze": "Phân tích bằng AI", "result": "Thông tin chính", "attention": "Cần kiểm tra", "found": "Thông tin tìm thấy", "actions": "Hành động tiếp theo", "unclear": "Thông tin thiếu hoặc chưa rõ", "support": "Nơi có thể hỗ trợ", "calendar": "Lịch tài chính", "phishing": "Kiểm tra lừa đảo", "consult": "Thẻ tư vấn", "ask": "Hỏi AI"},
}

SCHEMA = {
    "type": "object",
    "properties": {
        "document_type": {"type": "string", "enum": ["임대차계약서", "급여명세서", "공과금고지서", "기타"]},
        "summary": {"type": "string"},
        "highlights": {"type": "array", "minItems": 3, "maxItems": 3, "items": {"type": "object", "properties": {"label": {"type": "string"}, "value": {"type": "string"}}, "required": ["label", "value"]}},
        "money_items": {"type": "array", "items": {"type": "object", "properties": {"name": {"type": "string"}, "amount": {"type": "string"}, "evidence": {"type": "string"}}, "required": ["name", "amount", "evidence"]}},
        "date_items": {"type": "array", "items": {"type": "object", "properties": {"name": {"type": "string"}, "date": {"type": "string"}, "evidence": {"type": "string"}}, "required": ["name", "date", "evidence"]}},
        "risks": {"type": "array", "items": {"type": "object", "properties": {"level": {"type": "string", "enum": ["낮음", "확인 필요", "주의"]}, "title": {"type": "string"}, "explanation": {"type": "string"}, "evidence": {"type": "string"}}, "required": ["level", "title", "explanation", "evidence"]}},
        "next_actions": {"type": "array", "items": {"type": "string"}},
        "missing_or_unclear": {"type": "array", "items": {"type": "string"}},
        "consultation": {"type": "object", "properties": {"title": {"type": "string"}, "purpose": {"type": "string"}, "documents": {"type": "string"}, "korean_request": {"type": "string"}}, "required": ["title", "purpose", "documents", "korean_request"]},
    },
    "required": ["document_type", "summary", "highlights", "money_items", "date_items", "risks", "next_actions", "missing_or_unclear", "consultation"],
}


@st.cache_data
def load_data():
    def read(name):
        with (DATA_DIR / name).open(encoding="utf-8") as file:
            return json.load(file)
    return read("daeguide_document_analysis.json"), read("daeguide_multilingual_analysis_all.json"), read("daegu_support_centers.json")


def secret(name: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(name, default))
    except Exception:
        return default


def highlights(result: dict[str, Any]) -> list[dict[str, str]]:
    found = [{"label": x.get("name", "금액"), "value": x.get("amount", "-")} for x in result.get("money_items", [])[:2]]
    found += [{"label": x.get("name", "날짜"), "value": x.get("date", "-")} for x in result.get("date_items", [])[: 3 - len(found)]]
    return (found + [{"label": "확인 항목", "value": "원문 확인"}] * 3)[:3]


def consultation(result: dict[str, Any]) -> dict[str, str]:
    doc = result.get("document_type", "금융 문서")
    risk = (result.get("risks") or [{}])[0]
    title = {"급여명세서": "급여 공제 내역을 확인하고 싶습니다", "임대차계약서": "보증금 반환 조건을 확인하고 싶습니다", "공과금고지서": "공과금 부과 내역을 확인하고 싶습니다"}.get(doc, "문서 내용을 확인하고 싶습니다")
    return {"title": title, "purpose": risk.get("title", f"{doc} 내용 확인"), "documents": doc, "korean_request": f"{risk.get('explanation', '문서의 주요 조건')}에 대해 정확한 내용과 확인 방법을 설명해 주세요."}


def sample_result(doc_type, lang, docs, multi):
    key = next(k for k, v in docs.items() if v.get("document_type") == doc_type)
    result = json.loads(json.dumps(docs[key], ensure_ascii=False))
    result["highlights"] = highlights(result)
    result["consultation"] = consultation(result)
    translated = multi.get(key, {}).get("translations", {}).get(lang, {}) if lang != "ko" else {}
    if translated:
        result["summary"] = translated.get("summary", result["summary"])
        for i, text in enumerate(translated.get("risks", [])):
            if i < len(result.get("risks", [])):
                result["risks"][i]["explanation"] = text
        result["next_actions"] = translated.get("next_actions", result.get("next_actions", []))
    return result


def analyze(file_bytes: bytes, mime_type: str, lang: str) -> dict[str, Any]:
    api_key = secret("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Streamlit Secrets에 GEMINI_API_KEY를 먼저 등록해 주세요.")
    from google import genai
    from google.genai import types

    prompt = f"""한국에 거주하는 외국인을 위한 금융생활 문서 분석 도우미입니다. 첨부 문서를 읽고 결과를 {LANGUAGE_NAMES[lang]}로 작성하세요. document_type만 한국어 enum으로 유지하세요. 문서에 보이는 정보만 사용하고 추측하지 마세요. 불명확한 내용은 missing_or_unclear에 기록하세요. 연체료, 위약금, 보증금 반환, 자동갱신, 중도해지, 공제 증가 등 확인 조건을 원문 근거와 함께 설명하세요. highlights에는 가장 중요한 금액 또는 날짜 3개를 넣으세요. consultation.korean_request는 직원에게 보여줄 정중한 한국어 문장으로 작성하세요. 법률·금융 판단을 단정하지 마세요."""
    client = genai.Client(api_key=api_key)
    models = list(dict.fromkeys([secret("GEMINI_MODEL", "gemini-3.5-flash-lite"), "gemini-3.5-flash-lite"]))
    last_error = None
    for model in models:
        try:
            response = client.models.generate_content(model=model, contents=[types.Part.from_bytes(data=file_bytes, mime_type=mime_type), prompt], config=types.GenerateContentConfig(response_mime_type="application/json", response_json_schema=SCHEMA, temperature=0.1))
            return json.loads(response.text)
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"AI 분석에 실패했습니다. 잠시 후 다시 시도해 주세요. ({last_error})")


def centers_for(centers, region, doc_type):
    selected = []
    local = next((x for x in centers if x.get("region") == region), None)
    if local:
        selected.append(local)
    term = "법률구조공단" if doc_type == "임대차계약서" else "대구광역시가족센터"
    specialist = next((x for x in centers if term in x.get("name", "")), None)
    if specialist and specialist not in selected:
        selected.append(specialist)
    return selected[:2]


def phishing_check(text):
    patterns = {r"(즉시|긴급|오늘 안|지금 바로|계정.*정지)": "즉각적인 행동을 재촉합니다.", r"(송금|이체|입금).*(계좌|가상계좌)|계좌.*(송금|이체|입금)": "출처 확인 전 계좌이체를 요구합니다.", r"(앱|어플|프로그램).*(설치|다운로드)|설치.*(앱|어플)": "출처가 확인되지 않은 프로그램 설치를 유도할 수 있습니다.", r"(비밀번호|인증번호|보안카드|신분증|주민등록)": "개인정보나 인증정보를 요구할 수 있습니다.", r"https?://|www\.": "외부 링크가 포함되어 있습니다."}
    flags = [msg for pattern, msg in patterns.items() if re.search(pattern, text, re.I)]
    return min(98, 12 + 22 * len(flags)), flags


def css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;800&family=Noto+Sans+KR:wght@400;600;700;800&display=swap');
    html,body,[class*="css"]{font-family:'Noto Sans KR','DM Sans',sans-serif;color:#25302a}.stApp{background:radial-gradient(circle at 10% 0%,#f2f8d9 0,#fbf8ed 48%,#f7f3e9 100%)}.block-container{max-width:1180px;padding-top:4.75rem;padding-bottom:4rem}[data-testid="stSidebarUserContent"]{padding-top:4.75rem}.hero{background:rgba(255,253,248,.94);border:1px solid rgba(37,48,42,.12);border-radius:30px;padding:28px 32px;box-shadow:0 18px 50px rgba(66,82,68,.08);margin-bottom:18px}.brand{font:800 1.45rem 'DM Sans';letter-spacing:-.04em}.brand b{color:#829a80}.brand i{color:#d78f7c;font-style:normal}.eyebrow{color:#d97963;font:700 .74rem 'DM Sans';letter-spacing:.16em;margin-top:24px}.hero h1{font-size:clamp(2.15rem,4vw,4.2rem);line-height:1.02;letter-spacing:-.065em;margin:.5rem 0 1rem}.hero p{font-size:1.02rem;color:#526158}.result-head{background:#7f9281;color:#fffdf2;padding:22px 24px;border-radius:22px;margin:4px 0 18px}.result-head h2{margin:.2rem 0 0}.metric{background:#fffdfa;border:1px solid rgba(37,48,42,.12);border-radius:18px;padding:16px;min-height:98px}.metric small{color:#6a756e}.metric strong{display:block;font-size:1.15rem;margin-top:7px}.alert{background:#fff0e6;border:1px solid #e7bca5;border-radius:18px;padding:16px 18px;margin:12px 0 18px}.consult{background:#dce8f4;border:1px solid #b8c8d7;border-radius:22px;padding:20px 22px}.support{background:#f7efdf;border:1px solid #dfd1bc;border-radius:18px;padding:16px 18px;min-height:170px}.support p{min-height:42px;color:#627067}.note{font-size:.78rem;color:#6b756f}div.stButton>button{border-radius:999px;min-height:2.7rem}[data-testid="stSidebar"]{background:#f7f2e6}
    </style>""", unsafe_allow_html=True)


def show_result(result, lang, region, centers):
    t = UI[lang]
    doc_type = result.get("document_type", "기타")
    st.markdown(f"<div class='result-head'><small>{doc_type} · ANALYSIS COMPLETE</small><h2>{t['result']}</h2></div>", unsafe_allow_html=True)
    st.write(result.get("summary", ""))
    cols = st.columns(3)
    for col, item in zip(cols, result.get("highlights") or highlights(result)):
        col.markdown(f"<div class='metric'><small>{item.get('label','')}</small><strong>{item.get('value','-')}</strong></div>", unsafe_allow_html=True)
    risks = result.get("risks") or []
    if risks:
        r = risks[0]
        st.markdown(f"<div class='alert'><b>⚠ {t['attention']} · {r.get('title','')}</b><br>{r.get('explanation','')}<br><span class='note'>근거: {r.get('evidence','')}</span></div>", unsafe_allow_html=True)
    st.subheader(t["found"])
    rows = [{"항목": x.get("name", ""), "내용": x.get("amount", ""), "근거": x.get("evidence", "")} for x in result.get("money_items", [])]
    rows += [{"항목": x.get("name", ""), "내용": x.get("date", ""), "근거": x.get("evidence", "")} for x in result.get("date_items", [])]
    if rows:
        st.dataframe(rows, hide_index=True, width="stretch")
    left, right = st.columns(2)
    with left:
        st.subheader(t["actions"])
        for item in result.get("next_actions", []):
            st.markdown(f"- {item}")
        if result.get("missing_or_unclear"):
            with st.expander(t["unclear"]):
                for item in result["missing_or_unclear"]:
                    st.markdown(f"- {item}")
    with right:
        card = result.get("consultation") or consultation(result)
        st.markdown(f"<div class='consult'><small>DAEGU:IDE CONSULTATION CARD</small><h3>{card.get('title','')}</h3><b>상담 목적</b><p>{card.get('purpose','')}</p><b>준비 문서</b><p>{card.get('documents','')}</p><b>한국어 요청문</b><p>{card.get('korean_request','')}</p></div>", unsafe_allow_html=True)
        st.code(card.get("korean_request", ""), language=None)
    st.subheader(t["support"])
    st.caption("선택 지역과 문서 유형에 따른 규칙 기반 안내이며 실제 거리순 추천은 아닙니다.")
    recommended = centers_for(centers, region, doc_type)
    for col, center in zip(st.columns(max(1, len(recommended))), recommended):
        query = center.get("map_query", "").replace(" ", "+")
        col.markdown(f"<div class='support'><small>{center.get('region','광역')} · SUPPORT DATA</small><h4>{center.get('name','')}</h4><p>{center.get('field','')}</p><small>대표번호 {center.get('phone','-')}</small><br><a href='https://www.google.com/maps/search/?api=1&query={query}' target='_blank'>지도에서 보기</a> · <a href='{center.get('source','#')}' target='_blank'>공식 사이트</a></div>", unsafe_allow_html=True)
    st.session_state.last_result = result


def document_tab(lang, region, docs, multi, centers):
    t = UI[lang]
    st.markdown(f"<div class='hero'><div class='brand'>DAE<b>GU</b><i>:IDE</i></div><div class='eyebrow'>LIVE DOCUMENT ASSISTANT</div><h1>{t['headline']}</h1><p>{t['lead']}</p></div>", unsafe_allow_html=True)
    left, right = st.columns([.9, 1.45], gap="large")
    with left:
        with st.container(border=True):
            st.subheader(t["upload"])
            uploaded = st.file_uploader("JPG, PNG, WEBP, PDF · 최대 8MB", type=["jpg", "jpeg", "png", "webp", "pdf"])
            if uploaded and uploaded.size > 8 * 1024 * 1024:
                st.error("파일은 8MB 이하만 분석할 수 있습니다.")
            elif uploaded and st.button(t["analyze"], type="primary", width="stretch"):
                with st.spinner("금액, 날짜와 주의 조건을 확인하고 있어요..."):
                    try:
                        st.session_state.analysis = analyze(uploaded.getvalue(), uploaded.type, lang)
                        st.session_state.source = uploaded.name
                    except Exception as exc:
                        st.error(str(exc))
            st.markdown(f"**{t['sample']}**")
            for col, doc_type in zip(st.columns(3), DOCUMENTS):
                if col.button(DOCUMENTS[doc_type], width="stretch"):
                    st.session_state.analysis = sample_result(doc_type, lang, docs, multi)
                    st.session_state.source = f"{doc_type} 샘플"
            st.caption("실제 개인정보가 포함된 문서는 데모에 업로드하지 마세요.")
    with right:
        if st.session_state.get("analysis"):
            st.caption(st.session_state.get("source", "분석 결과"))
            show_result(st.session_state.analysis, lang, region, centers)
        else:
            with st.container(border=True):
                st.markdown("## ◇")
                st.subheader("분석 결과가 여기에 표시됩니다")
                st.write("문서를 업로드하거나 왼쪽에서 샘플을 선택해 보세요.")


def main():
    st.set_page_config(page_title="DAEGU:IDE", page_icon="◇", layout="wide")
    css()
    docs, multi, centers = load_data()
    with st.sidebar:
        st.markdown("## DAEGU:IDE")
        lang = LANGUAGES[st.selectbox("Language", list(LANGUAGES))]
        region = st.selectbox("거주 지역", ["광역", "중구", "동구", "서구", "남구", "북구", "수성구", "달서구", "달성군", "군위군"])
        st.caption(UI[lang]["tag"])
        if secret("GEMINI_API_KEY"):
            st.success("AI 분석 연결됨")
        else:
            st.warning("샘플 모드 · Gemini 키 미설정")
    tabs = st.tabs(["문서 도우미", UI[lang]["calendar"], UI[lang]["phishing"], UI[lang]["consult"], UI[lang]["ask"]])
    with tabs[0]:
        document_tab(lang, region, docs, multi, centers)
    with tabs[1]:
        st.subheader(UI[lang]["calendar"])
        result = st.session_state.get("last_result", {})
        if not result.get("date_items"):
            st.info("문서를 먼저 분석하면 찾은 날짜가 표시됩니다.")
        for item in result.get("date_items", []):
            st.markdown(f"### {item.get('date','-')} · {item.get('name','일정')}")
            st.caption("문서에서 찾은 일정입니다. 영구 저장과 알림은 고도화 기능입니다.")
    with tabs[2]:
        st.subheader(UI[lang]["phishing"])
        text = st.text_area("문자 내용", "[긴급] 미납 요금이 있습니다. 오늘 안에 아래 계좌로 680,000원을 송금하세요. 문의를 위해 앱을 설치하세요.", height=150)
        if st.button("위험 신호 확인", type="primary"):
            score, flags = phishing_check(text)
            if score >= 70:
                st.error(f"위험도 {score}")
            elif score >= 40:
                st.warning(f"위험도 {score}")
            else:
                st.success(f"위험도 {score}")
            for flag in flags or ["뚜렷한 위험 문구를 찾지 못했지만 발신처를 별도로 확인하세요."]:
                st.markdown(f"- {flag}")
            st.caption("현재 화면은 설명 가능한 규칙 기반 점검이며 학습 모델은 사전 실험 단계입니다.")
    with tabs[3]:
        st.subheader(UI[lang]["consult"])
        result = st.session_state.get("last_result") or st.session_state.get("analysis")
        if not result:
            st.info("문서를 먼저 분석하면 상담카드가 생성됩니다.")
        else:
            card = result.get("consultation") or consultation(result)
            st.markdown(f"<div class='consult'><small>DAEGU:IDE CONSULTATION CARD</small><h2>{card.get('title','')}</h2><b>상담 목적</b><p>{card.get('purpose','')}</p><b>준비 문서</b><p>{card.get('documents','')}</p><b>직원에게 보여줄 한국어</b><p>{card.get('korean_request','')}</p></div>", unsafe_allow_html=True)
            st.code(card.get("korean_request", ""), language=None)
    with tabs[4]:
        st.subheader(UI[lang]["ask"])
        result = st.session_state.get("last_result") or st.session_state.get("analysis")
        if not result:
            st.info("문서를 먼저 분석한 뒤 질문해 주세요.")
        else:
            question = st.text_input("질문", placeholder="예: 공제액이 왜 늘었나요?")
            if st.button("질문하기", type="primary") and question:
                risk = (result.get("risks") or [{}])[0]
                st.write(f"문서에서 확인된 내용은 ‘{risk.get('title','추가 확인 필요')}’입니다. {risk.get('explanation','담당 기관에 확인해 주세요.')}")
                st.caption("현재 질문 기능은 분석 결과를 바탕으로 한 시연입니다.")
    st.caption("DAEGU:IDE prototype · 본 결과는 참고용이며 금융·법률 판단을 대신하지 않습니다.")


if __name__ == "__main__":
    main()
