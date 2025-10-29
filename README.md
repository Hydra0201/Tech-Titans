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

## Hosting

Run the flask server by calling `flask run --port 5001`.
> We host on port 5001 because this is where the frontend is looking.

## Running Tests

To run the tests, call `pytest` from the app/ directory in console. If this doesn't work, first do `pip install -e .`

## Documentation

Run `mkdocs serve` from the top level directory. This serves the markdown files in the app/docs folder.

## Getting Help

Feel free to email roghan@purelymail.com with any questions unanswered by the documentation.

