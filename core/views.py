import json
import logging

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Avg, Count
from django.conf import settings

from core.models import WhaleTransaction

logger = logging.getLogger(__name__)


def dashboard(request):
    """Main whale alert dashboard page."""
    res = WhaleTransaction.objects.aggregate(
        total_count=Count('id'),
        total_volume=Sum('usd_value'),
        avg_size=Avg('usd_value'),
    )
    stats = {
        'total_whales': res['total_count'] or 0,
        'total_volume': res['total_volume'] or 0,
        'avg_size': res['avg_size'] or 0,
    }
    return render(request, 'core/dashboard.html', {'stats': stats})


def api_transactions(request):
    """REST endpoint returning recent whale transactions as JSON, with optional chain filter."""
    limit = int(request.GET.get('limit', 50))
    chain = request.GET.get('chain', '')
    qs = WhaleTransaction.objects.order_by('-timestamp')
    if chain:
        qs = qs.filter(chain=chain)
    txs = qs[:limit]
    return JsonResponse({'transactions': [tx.to_dict() for tx in txs]})


def api_stats(request):
    """Live stats endpoint, with optional chain filter."""
    chain = request.GET.get('chain', '')
    qs = WhaleTransaction.objects.all()
    if chain:
        qs = qs.filter(chain=chain)

    stats = qs.aggregate(
        total_count=Count('id'),
        total_volume=Sum('usd_value'),
        avg_size=Avg('usd_value'),
    )

    # Per-chain breakdown
    chain_breakdown = list(
        WhaleTransaction.objects.values('chain')
        .annotate(count=Count('id'), volume=Sum('usd_value'))
        .order_by('-volume')
    )

    return JsonResponse({
        'total_count': stats['total_count'] or 0,
        'total_volume': float(stats['total_volume'] or 0),
        'avg_size': float(stats['avg_size'] or 0),
        'chain_breakdown': [
            {
                'chain': b['chain'],
                'count': b['count'],
                'volume': float(b['volume'] or 0),
            }
            for b in chain_breakdown
        ],
    })


@csrf_exempt
@require_POST
def api_whale_report(request, pk):
    """
    Generate (or return cached) AI analysis for a whale transaction.
    Uses Claude via the Anthropic API.
    """
    try:
        tx = WhaleTransaction.objects.get(pk=pk)
    except WhaleTransaction.DoesNotExist:
        return JsonResponse({'error': 'Transaction not found'}, status=404)

    # Return cached report if available
    if tx.ai_summary:
        return JsonResponse({
            'cached': True,
            'summary': tx.ai_summary,
            'intent': tx.ai_intent,
            'impact': tx.ai_impact,
            'risk': tx.ai_risk,
            'tags': tx.ai_tags.split(',') if tx.ai_tags else [],
        })

    # Generate via Anthropic API
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        prompt = f"""You are a blockchain analyst specializing in on-chain whale intelligence.
Analyze this large cryptocurrency transaction and provide a concise report.

Transaction Details:
- Chain: {tx.chain} ({tx.get_chain_display()})
- Token: {tx.token_symbol}
- Amount: ${float(tx.usd_value):,.2f} USD
- From: {tx.from_address}
- To: {tx.to_address}
- Block: {tx.block_number}
- Hash: {tx.tx_hash}

Respond ONLY with valid JSON (no markdown, no backticks):
{{
  "summary": "2-sentence summary of what happened and why it matters",
  "intent": "1-sentence probable whale intent (accumulation, distribution, exchange deposit, DeFi, etc.)",
  "impact": "1-sentence likely short-term market impact",
  "risk": "HIGH, MEDIUM, or LOW",
  "tags": ["3 to 5 short signal tags"]
}}"""

        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = message.content[0].text.strip()
        # Strip any accidental markdown fences
        if raw.startswith('```'):
            raw = raw.split('\n', 1)[1].rsplit('```', 1)[0].strip()

        data = json.loads(raw)

        # Cache on the model
        tx.ai_summary = data.get('summary', '')
        tx.ai_intent = data.get('intent', '')
        tx.ai_impact = data.get('impact', '')
        tx.ai_risk = data.get('risk', 'MEDIUM')
        tx.ai_tags = ','.join(data.get('tags', []))
        tx.save(update_fields=['ai_summary', 'ai_intent', 'ai_impact', 'ai_risk', 'ai_tags'])

        return JsonResponse({
            'cached': False,
            'summary': tx.ai_summary,
            'intent': tx.ai_intent,
            'impact': tx.ai_impact,
            'risk': tx.ai_risk,
            'tags': data.get('tags', []),
        })

    except Exception as e:
        logger.error("AI report generation failed for tx %s: %s", pk, e)
        return JsonResponse({'error': str(e)}, status=500)
