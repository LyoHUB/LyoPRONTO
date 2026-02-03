# Contributor Documentation

## Testing

To install test dependencies, run
```
pip install .[dev]
```
inside the LyoPRONTO directory (next to `pyproject.toml`).

Execute 
```
pytest ./tests
```
to run all the tests; some that use `papermill` to generate documentation notebooks are marked, and you can exclude those with
```
pytest ./tests -m "not notebook"
```

## Documentation

Documentation build has different dependencies, installable by
```
pip install .[docs]
```

Run
```
mike deploy [name]
```
to deploy a docs version with ID `[name]`, which could be e.g. `v1.1.0` or `pr-10`, etc. Preview locally by navigating to `LyoPRONTO_folder/site`, then running
```
python -m http.server --bind localhost
```
to spin up a local HTTP server on your own machine. 

On pushing to master, GitHub actions will run
```
mike deploy dev
```
and on each tagged release will `mike deploy` the version number.


On the off chance that the documentation gets really broken, you can do the following to deploy a new version of it to GitHub Pages:

```
git fetch
git switch [branch with desired docs]
mike delete [broken docs version] # if necessary
mike deploy [new docs version] # if necessary
git switch gh-pages
git push origin gh-pages
```

### Helpful references for how to get documentation generated

https://realpython.com/python-project-documentation-with-mkdocs/ for a tutorial on MkDocs

https://entangled.github.io/mkdocs-plugin/setup/ because it would be nice to use for examples & tests

https://github.com/jimporter/mike?tab=readme-ov-file for versioning the docs


## Linting and formatting
The test suite is linted and formatted with Ruff, on default settings.

The main code base should also get the same treatment, but at present (2026-02-02) am waiting to do so: some of the code will be ugly upon formatting and should be rewritten to be less ugly.