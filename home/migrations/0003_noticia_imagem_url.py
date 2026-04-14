from django.db import migrations, models


# Links de Drive das 5 primeiras notícias. O matching por palavra-chave no
# título (case-insensitive) evita depender de IDs, que variam entre envs.
DRIVE_LINKS = [
    ('debate subfinanciament', 'https://drive.google.com/file/d/1yxpR-ip8mCUZGE6XGfv8YpAegPOKggZN/view?usp=drive_link'),
    ('lança plataforma', 'https://drive.google.com/file/d/1TY4Q2dSYWW6gluqkyNMfXmJ4lFTmlsQk/view?usp=drive_link'),
    ('manaus', 'https://drive.google.com/file/d/16E7EA_mc-vqVlSf1dYrN-muRFH6ROZ6i/view?usp=drive_link'),
    ('plataforma da fnp', 'https://drive.google.com/file/d/1eQYgu4IBffTDb_d81Mkzie5k3aG2FcaT/view?usp=drive_link'),
    ('seminário', 'https://drive.google.com/file/d/1MCwTzOACCrdTjX-xFORgOxBX2S_3BHZ0/view?usp=drive_link'),
]


def popular_urls(apps, schema_editor):
    Noticia = apps.get_model('home', 'Noticia')
    for keyword, url in DRIVE_LINKS:
        Noticia.objects.filter(titulo__icontains=keyword).update(imagem_url=url)


def reverter_urls(apps, schema_editor):
    Noticia = apps.get_model('home', 'Noticia')
    Noticia.objects.update(imagem_url=None)


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0002_municipio_rank_nacional_00_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='noticia',
            name='imagem_url',
            field=models.URLField(
                blank=True,
                help_text=(
                    "Cole o link de compartilhamento da imagem. Funciona com Google Drive "
                    "(o arquivo precisa estar como 'Qualquer pessoa com o link'), Imgur ou "
                    "qualquer URL pública direta (.jpg/.png)."
                ),
                max_length=500,
                null=True,
                verbose_name='Link da Imagem de Capa',
            ),
        ),
        migrations.RunPython(popular_urls, reverter_urls),
        migrations.RemoveField(
            model_name='noticia',
            name='imagem',
        ),
    ]
