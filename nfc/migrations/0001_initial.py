from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ('part', '0001_initial'),
        ('auth', '0001_initial'),
    ]
    operations = [
        migrations.CreateModel(
            name='NFCTagLink',
            fields=[
                ('id', models.AutoField(primary_key=True)),
                ('uid', models.CharField(max_length=64, unique=True)),
                ('linked_at', models.DateTimeField(auto_now_add=True)),
                ('part', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='nfc_tags', to='part.part')),
                ('linked_by', models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user')),
            ],
            options={'app_label': 'nfc'},
        ),
    ]