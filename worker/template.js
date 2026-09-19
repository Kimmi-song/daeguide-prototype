const ASSETS = __DAEGUIDE_ASSETS__;

const ANALYSIS_SCHEMA = {
  type: "object",
  properties: {
    document_type: { type: "string", enum: ["임대차계약서", "급여명세서", "공과금고지서", "기타"] },
    summary: { type: "string" },
    highlights: {
      type: "array", minItems: 3, maxItems: 3,
      items: {
        type: "object",
        properties: { label: { type: "string" }, value: { type: "string" } },
        required: ["label", "value"]
      }
    },
    money_items: {
      type: "array",
      items: {
        type: "object",
        properties: { name: { type: "string" }, amount: { type: "string" }, evidence: { type: "string" } },
        required: ["name", "amount", "evidence"]
      }
    },
    date_items: {
      type: "array",
      items: {
        type: "object",
        properties: { name: { type: "string" }, date: { type: "string" }, evidence: { type: "string" } },
        required: ["name", "date", "evidence"]
      }
    },
    risks: {
      type: "array",
      items: {
        type: "object",
        properties: {
          level: { type: "string", enum: ["낮음", "확인 필요", "주의"] },
          title: { type: "string" }, explanation: { type: "string" }, evidence: { type: "string" }
        },
        required: ["level", "title", "explanation", "evidence"]
      }
    },
    next_actions: { type: "array", items: { type: "string" } },
    missing_or_unclear: { type: "array", items: { type: "string" } },
    consultation: {
      type: "object",
      properties: {
        title: { type: "string" }, purpose: { type: "string" }, documents: { type: "string" }, korean_request: { type: "string" }
      },
      required: ["title", "purpose", "documents", "korean_request"]
    }
  },
  required: ["document_type", "summary", "highlights", "money_items", "date_items", "risks", "next_actions", "missing_or_unclear", "consultation"]
};

const LANGUAGE_NAMES = { ko: "쉬운 한국어", en: "plain English", zh: "简体中文", vi: "tiếng Việt dễ hiểu" };
const MODELS = ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-2.5-flash"];

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" }
  });
}

function bytesToBase64(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunk));
  }
  return btoa(binary);
}

function readOutputText(payload) {
  for (const step of payload.steps || []) {
    if (step.type !== "model_output") continue;
    for (const item of step.content || []) if (item.type === "text" && item.text) return item.text;
  }
  return payload.output_text || "";
}

async function analyzeDocument(request, env) {
  if (!env.GEMINI_API_KEY) return json({ error: "AI 분석 설정이 아직 완료되지 않았습니다." }, 503);

  let form;
  try { form = await request.formData(); }
  catch { return json({ error: "업로드 형식을 확인해 주세요." }, 400); }

  const file = form.get("file");
  const language = String(form.get("language") || "ko");
  if (!(file instanceof File)) return json({ error: "분석할 파일을 선택해 주세요." }, 400);
  if (file.size > 8 * 1024 * 1024) return json({ error: "파일은 8MB 이하만 분석할 수 있습니다." }, 413);

  const allowed = new Set(["image/jpeg", "image/png", "image/webp", "application/pdf"]);
  if (!allowed.has(file.type)) return json({ error: "JPG, PNG, WEBP 또는 PDF 파일만 지원합니다." }, 415);

  const targetLanguage = LANGUAGE_NAMES[language] || LANGUAGE_NAMES.ko;
  const prompt = `당신은 한국에 거주하는 외국인을 위한 금융생활 문서 분석 도우미입니다. 첨부 문서의 글자를 직접 읽고 분석 결과를 ${targetLanguage}로 작성하세요. 문서 종류 값만은 반드시 한국어 enum 값으로 유지하세요. 문서에 실제로 보이는 정보만 사용하고 금액·날짜·조건을 추측하지 마세요. OCR이 불명확한 부분은 missing_or_unclear에 기록하세요. 보증금 반환, 연체료, 위약금, 자동갱신, 중도해지, 공제 증가 등 불리하거나 확인할 조건을 근거 원문과 함께 설명하세요. highlights는 사용자가 가장 먼저 봐야 할 금액 또는 날짜 3개로 만드세요. consultation의 korean_request는 기관이나 회사 직원에게 바로 보여줄 수 있는 정중한 한국어 문장으로 작성하세요. 이 결과는 참고용이며 법률·금융 판단을 단정하지 마세요.`;
  const base64 = bytesToBase64(await file.arrayBuffer());
  let lastMessage = "AI 분석에 실패했습니다.";

  for (const model of MODELS) {
    const response = await fetch("https://generativelanguage.googleapis.com/v1beta/interactions", {
      method: "POST",
      headers: { "content-type": "application/json", "x-goog-api-key": env.GEMINI_API_KEY },
      body: JSON.stringify({
        model,
        input: [
          { type: "text", text: prompt },
          { type: file.type === "application/pdf" ? "document" : "image", data: base64, mime_type: file.type }
        ],
        response_format: { type: "text", mime_type: "application/json", schema: ANALYSIS_SCHEMA }
      })
    });

    const payload = await response.json().catch(() => ({}));
    if (response.ok) {
      const output = readOutputText(payload);
      try { return json({ analysis: JSON.parse(output), model }); }
      catch { lastMessage = "AI 결과를 화면 형식으로 변환하지 못했습니다."; }
    } else {
      lastMessage = payload.error?.message || lastMessage;
      if (![429, 500, 503].includes(response.status)) break;
    }
  }

  console.error("Gemini analysis failed:", lastMessage);
  return json({ error: "현재 AI 요청이 많습니다. 잠시 후 다시 시도해 주세요." }, 502);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === "POST" && url.pathname === "/api/analyze") return analyzeDocument(request, env);
    if (request.method !== "GET" && request.method !== "HEAD") return new Response("Method not allowed", { status: 405 });

    const asset = ASSETS[url.pathname];
    if (!asset) return new Response("Not found", { status: 404 });
    const headers = { "content-type": asset.contentType, "cache-control": "no-store" };
    if (url.pathname === "/" || url.pathname === "/index.html") {
      headers["content-security-policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self'; connect-src 'self' https://generativelanguage.googleapis.com; img-src 'self' data:; base-uri 'none'; frame-ancestors 'self'";
    }
    return new Response(request.method === "HEAD" ? null : asset.body, { headers });
  }
};
