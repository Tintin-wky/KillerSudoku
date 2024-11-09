# Killer sudoku solver

## Summary

Solver for Killer sudokus, details [here](https://en.wikipedia.org/wiki/Killer_sudoku).

Uses *PuLP* optimization library, details [here](https://pythonhosted.org/PuLP/)

WIP - get puzzle-sovler working that doesn't rely on external optimization libraries

Includes scraper and parser for dailykillersudoku.com, puzzles [here](https://www.dailykillersudoku.com)

## Dependencies

```bash
pip install pulp
pip install numpy
pip install matplotlib
```

## Run tests 

```bash
pytest .
```

## Run code
change your_sudoku_Id to something like ***26274*** which you can find on [dailykillersudoku.com](https://www.dailykillersudoku.com)

```bash
python3 killer_sudoku/killer_client.py --id your_sudoku_Id
```
