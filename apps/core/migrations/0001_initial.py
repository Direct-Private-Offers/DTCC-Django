import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='IdempotencyKey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=128)),
                ('method', models.CharField(max_length=8)),
                ('path', models.CharField(max_length=256)),
                ('response', models.JSONField()),
                ('expires_at', models.DateTimeField(db_index=True)),
            ],
            options={
                'indexes': [
                    models.Index(fields=['expires_at'], name='core_idemp_expires_1c8f19_idx'),
                ],
                'unique_together': {('key', 'path')},
            },
        ),
        migrations.CreateModel(
            name='ApiSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('jti', models.CharField(db_index=True, max_length=64)),
                ('subject', models.CharField(db_index=True, max_length=128)),
                ('first_seen', models.DateTimeField(auto_now_add=True)),
                ('last_seen', models.DateTimeField(auto_now=True)),
                ('ip', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True, null=True)),
                ('request_count', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='WebhookReplay',
            fields=[
                ('nonce', models.CharField(max_length=128, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                'indexes': [
                    models.Index(fields=['created_at'], name='core_webho_created_2a2b1f_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='WebhookEvent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('source', models.CharField(choices=[('euroclear', 'Euroclear'), ('clearstream', 'Clearstream'), ('chainlink', 'Chainlink')], max_length=16)),
                ('event_type', models.CharField(max_length=64)),
                ('event_data', models.JSONField()),
                ('reference', models.CharField(blank=True, max_length=128, null=True)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('PROCESSING', 'Processing'), ('PROCESSED', 'Processed'), ('FAILED', 'Failed')], default='PENDING', max_length=16)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
                ('error_message', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'indexes': [
                    models.Index(fields=['source', 'status'], name='core_webho_source_5d2f6e_idx'),
                    models.Index(fields=['status', 'created_at'], name='core_webho_status_0c4f7b_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='RedirectEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('route', models.CharField(db_index=True, max_length=64)),
                ('target_url', models.URLField(max_length=512)),
                ('query_params', models.JSONField(blank=True, null=True)),
                ('referrer', models.TextField(blank=True, null=True)),
                ('ip', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True, null=True)),
                ('request_id', models.CharField(blank=True, max_length=64, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                'indexes': [
                    models.Index(fields=['route', 'created_at'], name='core_redir_route_4cc7f9_idx'),
                ],
            },
        ),
    ]
