# Generated by Django 4.0.1 on 2023-03-23 04:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('songs', '0029_alter_comment_create_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='song',
            name='genre',
            field=models.PositiveSmallIntegerField(blank=True, choices=[('electronic-techno', 'Electronic - Techno'), ('electronic-dance', 'Electronic - Dance'), ('electronic-ambient', 'Electronic - Ambient'), ('trance-general', 'Trance - General'), ('electronic-other', 'Electronic - Other'), ('electronic-general', 'Electronic - General'), ('electronic-drum-and-bass', 'Electronic - Drum & Bass'), ('electronic-house', 'Electronic - House'), ('electronic-rave', 'Electronic - Rave'), ('trance-dream', 'Trance - Dream'), ('electronic-breakbeat', 'Electronic - Breakbeat'), ('electronic-industrial', 'Electronic - Industrial'), ('electronic-hardcore', 'Electronic - Hardcore'), ('chillout', 'Chillout'), ('trance-goa', 'Trance - Goa'), ('electronic-jungle', 'Electronic - Jungle'), ('trance-acid', 'Trance - Acid'), ('electronic-idm', 'Electronic - IDM'), ('electronic-progressive', 'Electronic - Progressive'), ('electronic-gabber', 'Electronic - Gabber'), ('electronic-minimal', 'Electronic - Minimal'), ('trance-hard', 'Trance - Hard'), ('trance-progressive', 'Trance - Progressive'), ('trance-tribal', 'Trance - Tribal'), ('chiptune', 'Chiptune'), ('demostyle', 'Demostyle'), ('one-hour-compo', 'One-Hour Compo'), ('pop-general', 'Pop - General'), ('pop-synth', 'Pop - Synth'), ('pop-soft', 'Pop - Soft'), ('rock-general', 'Rock - General'), ('rock-soft', 'Rock - Soft'), ('rock-hard', 'Rock - Hard'), ('funk', 'Funk'), ('disco', 'Disco'), ('ballad', 'Ballad'), ('easy-listening', 'Easy Listening'), ('video-game', 'Video Game'), ('orchestral', 'Orchestral'), ('classical', 'Classical'), ('piano', 'Piano'), ('fantasy', 'Fantasy'), ('soundtrack', 'Soundtrack'), ('comedy', 'Comedy'), ('medieval', 'Medieval'), ('spiritual', 'Spiritual'), ('religious', 'Religious'), ('experimental', 'Experimental'), ('new-age', 'New Age'), ('folk', 'Folk'), ('country', 'Country'), ('bluegrass', 'Bluegrass'), ('world', 'World'), ('world-latin', 'World - Latin'), ('fusion', 'Fusion'), ('vocal-montage', 'Vocal Montage'), ('other', 'Other'), ('alternative', 'Alternative'), ('gothic', 'Gothic'), ('punk', 'Punk'), ('metal-general', 'Metal - General'), ('metal-extreme', 'Metal - Extreme'), ('grunge', 'Grunge'), ('jazz-general', 'Jazz - General'), ('jazz-modern', 'Jazz - Modern'), ('jazz-acid', 'Jazz - Acid'), ('blues', 'Blues'), ('swing', 'Swing'), ('big-band', 'Big Band'), ('hip-hop', 'Hip-Hop'), ('reggae', 'Reggae'), ('r-n-b', 'R&B'), ('soul', 'Soul'), ('ska', 'Ska'), ('christmas', 'Christmas'), ('halloween', 'Halloween')], db_index=True, null=True),
        ),
    ]
