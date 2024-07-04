# Fixpoint

Open source infra for reliable multi-step AI workflows.

Build and connect multiple AI agents that know your data and work together to
run autonomous or human-in-the-loop workflows, so that the humans can focus on
more important work.


## Development

We use Poetry, which manages its own virtual environments. To install the
package locally for development:

```
# Installs both the dev and prod dependencies
poetry install

# installs just dev dependencies
poetry install --only main
```

To install the package in an editable mode, so you can import it like `import
fixpoint` from any other code in your virtual-env:

```
pip install -e .
```

### Git hooks

Set up your Githooks via:

```
git config core.hooksPath githooks/

npm install -g lint-staged
```


## Building and publishin

To build the Python package, from the root of the repo just run:

```bash
poetry build
```

This will build a wheel and a tarball in the `dist/` directory.

If you want to test the package locally, you can install the wheel, preferably
in a new standalone virtual environment.

```bash
python3.12 -m venv /tmp/venv
source /tmp/ven/bin/activate
# we use a wildcard so we don't care what version
pip install ./dist/fixpoint-*-py3-none-any.whl

# or install some specific extra dependencies
# Note, you will need to fully specify the wheel, without a wildcard
pip install './dist/fixpoint-0.1.0-py3-none-any.whl[dev]'
```

### Publishing to PyPi

In general, you should not publish from the command line, but instead through
CI. See the `.github/workflows/pypi-release-*.yml` files for the CI actions to
publish to PyPi.

If you want to publish from the CLI, you can configure Poetry for publishing to
the test PyPi and prod PyPi respectively:

```bash
poetry config pypi-token.testpypi <your-test-pypi-token>
```

To publish to the test index:

```bash
poetry publish --repository testpypi
```
