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

## Documentation

Run `mkdocs serve` from the top level directory.

## Getting Help

Feel free to email roghan@purelymail.com with any questions unanswered by the documentation.