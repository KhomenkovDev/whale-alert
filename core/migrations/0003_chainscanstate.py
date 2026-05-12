from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0002_multichain_ai'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChainScanState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chain', models.CharField(choices=[('ETH', 'Ethereum'), ('BNB', 'BNB Chain'), ('POL', 'Polygon'), ('AVAX', 'Avalanche')], max_length=10, unique=True)),
                ('last_scanned_block', models.BigIntegerField(default=0)),
                ('last_scanned_at', models.DateTimeField(auto_now=True)),
                ('is_scanning', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Chain Scan State',
                'verbose_name_plural': 'Chain Scan States',
            },
        ),
    ]
