# Generated migration for DomainConfiguration model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('url_shortener', '0001_initial'),  # Adjust this based on your last migration
    ]

    operations = [
        migrations.CreateModel(
            name='DomainConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('domain', models.CharField(db_index=True, help_text="Fully qualified domain name (e.g., 'forms.clientbusiness.com')", max_length=255, unique=True)),
                ('account_id', models.IntegerField(db_index=True, help_text='CRM Account ID that owns this domain')),
                ('domain_type', models.CharField(choices=[('forms', 'Forms Domain'), ('payment', 'Payment Domain'), ('other', 'Other')], default='forms', help_text='Type of domain (forms, payment, etc.)', max_length=20)),
                ('is_verified', models.BooleanField(default=False, help_text='Whether domain DNS is verified and points to this server')),
                ('is_active', models.BooleanField(default=True, help_text='Whether domain configuration is active')),
                ('ssl_status', models.CharField(choices=[('pending', 'Pending'), ('active', 'Active'), ('failed', 'Failed'), ('expired', 'Expired')], default='pending', help_text='SSL certificate status', max_length=20)),
                ('configured_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('ssl_issued_at', models.DateTimeField(blank=True, help_text='When SSL certificate was issued', null=True)),
                ('ssl_expires_at', models.DateTimeField(blank=True, help_text='When SSL certificate expires', null=True)),
                ('use_caddy', models.BooleanField(default=True, help_text='Use Caddy for automatic SSL (vs manual nginx config)')),
                ('notes', models.TextField(blank=True, help_text='Optional admin notes about this domain')),
            ],
            options={
                'db_table': 'domain_configurations',
                'ordering': ['-configured_at'],
            },
        ),
        migrations.AddIndex(
            model_name='domainconfiguration',
            index=models.Index(fields=['domain'], name='domain_conf_domain_idx'),
        ),
        migrations.AddIndex(
            model_name='domainconfiguration',
            index=models.Index(fields=['account_id'], name='domain_conf_account_idx'),
        ),
        migrations.AddIndex(
            model_name='domainconfiguration',
            index=models.Index(fields=['is_active', 'is_verified'], name='domain_conf_active_verified_idx'),
        ),
    ]
