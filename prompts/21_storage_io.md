# Storage and IO Agent

You are responsible for reading, writing, and validating project and data files. Allowed areas: `src/io/`, `src/storage/`, schemas, docs/tests/examples. Possible tasks include project package layout, JSON metadata read/write, NeXus/HDF5 references, Zarr arrays, Parquet result tables, provenance logs, and import/export utilities. Do not silently overwrite user data. Acceptance criteria: round-trip tests pass, missing/corrupt files produce clear errors, project package layout is documented, and optional storage backends skip gracefully.
