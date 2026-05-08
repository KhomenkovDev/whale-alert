from django.contrib import admin
from core.models import WhaleTransaction


@admin.register(WhaleTransaction)
class WhaleTransactionAdmin(admin.ModelAdmin):
    list_display = ['short_tx', 'token_symbol', 'usd_value', 'from_address', 'to_address', 'timestamp']
    list_filter = ['token_symbol', 'timestamp']
    search_fields = ['tx_hash', 'from_address', 'to_address']
    readonly_fields = ['discovered_at']
    ordering = ['-timestamp']
