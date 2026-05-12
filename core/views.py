import json
import logging

from django.conf import settings
from django.db.models import Avg, Count, Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from core.models import WhaleTransaction

logger = logging.getLogger(__name__)


def dashboard(request):
    res = WhaleTransaction.objects.aggregate(
        total_count=Count("id"),
        total_volume=Sum("usd_value"),
        avg_size=Avg("usd_value"),
    )
    stats = {
        "total_whales": res["total_count"] or 0,
        "total_volume": res["total_volume"] or 0,
        "avg_size": res["avg_size"] or 0,
    }
    return render(
        request,
        "core/dashboard.html",
        {
            "stats": stats,
            "threshold": f"{settings.WHALE_THRESHOLD_USD:,}",
        },
    )


def api_transactions(request):
    limit = int(request.GET.get("limit", 50))
    chain = request.GET.get("chain", "")
    qs = WhaleTransaction.objects.order_by("-timestamp")
    if chain:
        qs = qs.filter(chain=chain)
    txs = qs[:limit]
    return JsonResponse({"transactions": [tx.to_dict() for tx in txs]})


def api_stats(request):
    chain = request.GET.get("chain", "")
    qs = WhaleTransaction.objects.all()
    if chain:
        qs = qs.filter(chain=chain)

    stats = qs.aggregate(
        total_count=Count("id"),
        total_volume=Sum("usd_value"),
        avg_size=Avg("usd_value"),
    )

    chain_breakdown = list(
        WhaleTransaction.objects.values("chain")
        .annotate(count=Count("id"), volume=Sum("usd_value"))
        .order_by("-volume")
    )

    return JsonResponse(
        {
            "total_count": stats["total_count"] or 0,
            "total_volume": float(stats["total_volume"] or 0),
            "avg_size": float(stats["avg_size"] or 0),
            "chain_breakdown": [
                {
                    "chain": b["chain"],
                    "count": b["count"],
                    "volume": float(b["volume"] or 0),
                }
                for b in chain_breakdown
            ],
        }
    )


@ratelimit(key="ip", rate=settings.AI_REPORT_RATE_LIMIT, method="POST", block=True)
@csrf_exempt
@require_POST
def api_whale_report(request, pk):
    try:
        tx = WhaleTransaction.objects.get(pk=pk)
    except WhaleTransaction.DoesNotExist:
        return JsonResponse({"error": "Transaction not found"}, status=404)

    if tx.ai_summary:
        return JsonResponse(
            {
                "cached": True,
                "summary": tx.ai_summary,
                "intent": tx.ai_intent,
                "impact": tx.ai_impact,
                "risk": tx.ai_risk,
                "tags": tx.ai_tags.split(",") if tx.ai_tags else [],
            }
        )

    try:
        from google import genai
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        prompt = f"""You are a blockchain analyst specializing in on-chain whale intelligence.
Analyze this large cryptocurrency transaction and provide a concise report.

Transaction Details:
- Chain: {tx.chain} ({tx.get_chain_display()})
- Token: {tx.token_symbol}
- Amount: ${float(tx.usd_value):,.2f} USD
- From: {tx.from_address}
- To: {tx.to_address}
- Hash: {tx.tx_hash}

Respond ONLY with valid JSON (no markdown, no backticks):
{{
  "summary": "2-sentence summary of what happened and why it matters",
  "intent": "1-sentence probable whale intent (accumulation, distribution, exchange deposit, DeFi)",
  "impact": "1-sentence likely short-term market impact",
  "risk": "HIGH, MEDIUM, or LOW",
  "tags": ["3 to 5 short signal tags"]
}}"""

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )

        data = json.loads(response.text)

        tx.ai_summary = data.get("summary", "")
        tx.ai_intent = data.get("intent", "")
        tx.ai_impact = data.get("impact", "")
        tx.ai_risk = data.get("risk", "MEDIUM")
        tx.ai_tags = ",".join(data.get("tags", []))
        tx.save(update_fields=["ai_summary", "ai_intent", "ai_impact", "ai_risk", "ai_tags"])

        return JsonResponse(
            {
                "cached": False,
                "summary": tx.ai_summary,
                "intent": tx.ai_intent,
                "impact": tx.ai_impact,
                "risk": tx.ai_risk,
                "tags": data.get("tags", []),
            }
        )

    except Exception as e:
        logger.error("AI report generation failed for tx %s: %s", pk, e)
        return JsonResponse({"error": str(e)}, status=500)


def health_check(request):
    from django.db import connection

    db_ok = True
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        db_ok = False

    import redis

    redis_ok = True
    try:
        r = redis.from_url(settings.CELERY_BROKER_URL)
        r.ping()
    except Exception:
        redis_ok = False

    return JsonResponse(
        {
            "status": "ok" if db_ok and redis_ok else "degraded",
            "database": "ok" if db_ok else "error",
            "redis": "ok" if redis_ok else "error",
        }
    )
