# Fixpoint

Open source infra for reliable multi-step AI workflows.

Build and connect multiple AI agents that know your data and work together to
run autonomous or human-in-the-loop workflows, so that the humans can focus on
more important work.


## Development

### Virtual Env

To create a virtual environment called `venv`:

```
# Create the virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Upgrade pip to latest version (in part so we can do editable installs), and
# then install Poetry, which is how we manage the package.
pip install --upgrade pip
pip install poetry
```

To install the package locally for development:

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
