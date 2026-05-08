from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='whaletransaction',
            name='chain',
            field=models.CharField(
                choices=[('ETH', 'Ethereum'), ('BNB', 'BNB Chain'), ('POL', 'Polygon'), ('AVAX', 'Avalanche')],
                default='ETH',
                db_index=True,
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='whaletransaction',
            name='explorer_url',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
        migrations.AddField(
            model_name='whaletransaction',
            name='ai_summary',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='whaletransaction',
            name='ai_intent',
            field=models.CharField(blank=True, default='', max_length=300),
        ),
        migrations.AddField(
            model_name='whaletransaction',
            name='ai_impact',
            field=models.CharField(blank=True, default='', max_length=300),
        ),
        migrations.AddField(
            model_name='whaletransaction',
            name='ai_risk',
            field=models.CharField(blank=True, default='', max_length=10),
        ),
        migrations.AddField(
            model_name='whaletransaction',
            name='ai_tags',
            field=models.CharField(blank=True, default='', max_length=300),
        ),
    ]
