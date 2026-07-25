import factory

from artists.models import Artist

class ArtistFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Artist

    @factory.post_generation
    def songs(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for song in extracted:
                self.songs.add(song)
            # Refresh from DB to sync any signal-updated fields before factory re-saves
            self.refresh_from_db()

    name = factory.Sequence(lambda n: 'Artist %d' % n)