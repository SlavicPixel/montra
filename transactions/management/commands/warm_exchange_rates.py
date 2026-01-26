from django.core.management.base import BaseCommand
from django.core.cache import cache
from montra.exchange_rates import get_top_rates, _cache_key, TOP_CURRENCIES


class Command(BaseCommand):
    help = "Warm Redis cache with top exchange rates."

    def add_arguments(self, parser):
        parser.add_argument("--base", default="EUR")

    def handle(self, *args, **opts):
        base = (opts["base"] or "EUR").upper()

        key = _cache_key(base, TOP_CURRENCIES)
        cache.delete(key)

        payload = get_top_rates(base=base)

        count = len((payload or {}).get("rates") or {})
        self.stdout.write(
            self.style.SUCCESS(
                f"Warmed FX cache for {base} ({count} rates). source={payload.get('source')}"
            )
        )
