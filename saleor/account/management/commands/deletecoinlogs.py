
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from ....account.models import BalanceEvent, User


class Command(BaseCommand):
    help = "Delete coin logs before a certain time"

    def add_arguments(self, parser):
        # 添加命令行参数
        parser.add_argument('date_cutoff', type=str, help='The date cutoff in YYYY-MM-DD format')

    def handle(self, *args, **options):
        try:
            date_cutoff_str = options['date_cutoff']
            try:
                # 将字符串日期转换为 datetime 对象
                date_cutoff = datetime.strptime(date_cutoff_str, '%Y-%m-%d')
            except ValueError as e:
                raise CommandError('Invalid date format. Please use YYYY-MM-DD.')

            # 使用 timezone 确保 datetime 对象是 aware 的（包含时区信息）
            aware_date_cutoff = timezone.make_aware(date_cutoff, timezone.get_default_timezone())
            
            u = BalanceEvent.objects.filter(date__lt=aware_date_cutoff)

            deleted_count, _ = u.delete()

            self.stdout.write(
                self.style.SUCCESS(
                    "Deleted %d logs"
                    % deleted_count
                )
            )
        except Exception as ex:
            self.stdout.write(
                self.style.WARNING(
                    ex.__str__()
                )
            )
