# Exercise Catalog Media

The bundled exercise thumbnails and animation GIFs are:

`© Gym visual — https://gymvisual.com/`

They are included in this application under the developer's separately
obtained authorization. Media paths and attribution are also stored per
exercise in `assets/catalog/exercises.db`.

Exercise metadata originates from the pinned dataset revision:

`hasaneyldrm/exercises-dataset@7455efae41b330c265e7cd4b78dfa848e7ce5ebd`

The catalog database is the runtime source of truth. To add an exercise:

1. Copy `<source_id>.jpg` to `assets/catalog/thumbs/`.
2. Copy `<source_id>.gif` to `assets/catalog/gifs/`.
3. Insert or update its row in `assets/catalog/exercises.db` using
   `tools/catalog_schema.sql` as the schema/reference.
4. Start the app once; `init_db()` incrementally syncs the packaged catalog
   into the writable user database.
