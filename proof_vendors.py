import os, json, time, uuid, pathlib, sys
from dotenv import load_dotenv
from openai import OpenAI

# --- setup ---
load_dotenv()
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
)
LOGDIR = pathlib.Path("logs")
LOGDIR.mkdir(parents=True, exist_ok=True)

EXTRA_HEADERS = {
    "HTTP-Referer": "https://github.com/GpmarquesUK/FlashSoft",
    "X-Title": "FlashSoft-Vendors-Proof"
}

# (vendor, route, prompt)
MODELS = [
    ("OpenAI",   "openai/gpt-4o",                 "Return the word OK."),
    ("Anthropic","anthropic/claude-sonnet-4.5",   "Return the word OK."),
    ("xAI",      "x-ai/grok-4-fast",              "Return the word OK."),
    ("Google",   "google/gemini-2.5-pro",         "Return the word OK.")
]

def one_probe(vendor: str, route: str, prompt: str, nonce: str):
    """
    Critério de sucesso: o campo resp.model retornado pelo OpenRouter
    deve ser exatamente igual ao route solicitado.
    """
    try:
        resp = client.chat.completions.create(
            model=route,
            messages=[
                {"role": "system", "content": "Answer briefly."},
                {"role": "user", "content": f"{prompt} Nonce: {nonce}"}
            ],
            temperature=0,
            max_tokens=16,
            extra_headers=EXTRA_HEADERS,
            timeout=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "60")),
        )
        text = (resp.choices[0].message.content or "").strip()
        resp_model = getattr(resp, "model", None)
        usage = getattr(resp, "usage", None)
        usage_dict = None
        try:
            usage_dict = usage and usage.model_dump()
        except Exception:
            try:
                usage_dict = dict(usage)
            except Exception:
                usage_dict = None

        route_ok = (resp_model == route)

        return {
            "vendor": vendor,
            "expected_route": route,
            "resp_model": resp_model,
            "resp_id": getattr(resp, "id", None),
            "usage": usage_dict,
            "text": text,
            "route_ok": bool(route_ok),
            "error": None
        }
    except Exception as e:
        return {
            "vendor": vendor,
            "expected_route": route,
            "resp_model": None,
            "resp_id": None,
            "usage": None,
            "text": None,
            "route_ok": False,
            "error": repr(e)
        }

def main():
    run_id = f"vendors-proof-{int(time.time())}-{uuid.uuid4().hex[:8]}"
    nonce = uuid.uuid4().hex
    results = []

    print(f"[proof] run_id={run_id} nonce={nonce}")
    for vendor, route, prompt in MODELS:
        print(f"→ probing {vendor:9s} | {route} ...", end=" ")
        r = one_probe(vendor, route, prompt, nonce)
        results.append(r)
        print("PASS" if r["route_ok"] else "FAIL")

    # Persist artifacts
    proof_json = LOGDIR / f"{run_id}.json"
    proof_md   = LOGDIR / "VENDORS_PROOF.md"

    with open(proof_json, "w", encoding="utf-8") as f:
        json.dump({"run_id": run_id, "nonce": nonce, "results": results}, f, ensure_ascii=False, indent=2)

    lines = []
    lines.append(f"# Vendors Proof — {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- run_id: `{run_id}`  |  nonce: `{nonce}`")
    lines.append("")
    lines.append("| Vendor  | Expected Route               | Response Model            | Resp ID            | Tokens (in/out) | Status |")
    lines.append("|---------|------------------------------|---------------------------|--------------------|-----------------|--------|")
    for r in results:
        in_t = out_t = "-"
        if r["usage"]:
            in_t  = r["usage"].get("prompt_tokens", "-")
            out_t = r["usage"].get("completion_tokens", "-")
        status = "PASS" if r["route_ok"] else "FAIL"
        lines.append(
            f"| {r['vendor']:<7} | {r['expected_route']:<28} | {str(r['resp_model']):<25} | "
            f"{str(r['resp_id']):<18} | {in_t}/{out_t:<11} | {status} |"
        )
    lines.append("\n---\n")
    with open(proof_md, "a", encoding="utf-8") as f:
        f.write("\n".join(lines))

    passed = sum(1 for r in results if r["route_ok"])
    total = len(results)
    print(f"\nSummary: {passed}/{total} PASSED")
    if passed != total:
        print("Details:")
        for r in results:
            if not r["route_ok"]:
                print(f"- {r['vendor']} | expected={r['expected_route']} | got={r['resp_model']} | error={r['error']}")
    sys.exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()
