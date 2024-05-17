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
