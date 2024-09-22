"""Relabel all order numbers. This is a workaround on current concurrency issue."""
from datetime import datetime
from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from ....account.models import Order


class Command(BaseCommand):
    help = "Relabel duplicated"

    def add_arguments(self, parser: CommandParser) -> None:
        return super().add_arguments(parser)

    def relabel_orders(self):
        first = Order.objects.order_by("created_at").first()
        duplicated = []
        number_set = set()
        assert first is not None
        current_year_month = datetime(
            first.created_at.year,
            first.created_at.month,
            1,
            tzinfo=first.created_at.tzinfo,
        )
        for order in Order.objects.iterator():
            order_year_month = datetime(
                order.created_at.year,
                order.created_at.month,
                1,
                tzinfo=order.created_at.tzinfo,
            )

            if order_year_month > current_year_month:
                for i, order in enumerate(duplicated):
                    order.number = i + len(number_set) + 1
                    order.save(update_fields=["number"])
                duplicated.clear()
                number_set.clear()
                current_year_month = order_year_month

            if order.number in number_set:
                duplicated.append(order)
            else:
                number_set.add(order.number)

    def handle(self, *args: Any, **options: Any):
        self.relabel_orders()
