# CarbonBalance Prototype



## Setup

After cloning project, run:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install -r requirements.txt
```
This will:
- Create a virtual environment in `.venv/`
- Activate the venv
- Install project in editable mode (so files in `tests/` can import from `src/`)
- Install all required dependencies

## Installing New Dependencies

If you install a new dependency, do the following to update requirements.txt:
`pip freeze > requirements.txt`

## Running Tests

To run the tests, run `pytest` in console. If this doesn't work, first do `pip install -e .`


## .gitignore

You should create a .gitignore file so that you can define files you don't want to get pushed to github.
Mine looks like this currently:
```
.venv/  
venv/
__pycache__/
*.py[cod]
.vscode/
.pytest_cache/
*.egg-info/
dist/
build/
```
