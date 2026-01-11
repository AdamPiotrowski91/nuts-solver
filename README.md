# Nut Sorter Solver

There is this mobile game, `Nut Sorter`, which is generally rising in difficulty slowly, with pace. But there are those levels where you do not see all the nuts at once. And unfortunately, the gimmic for them is to try different things for as long as you do not know what some nuts are and then solve as any other. Basically - ad-watch-generator-levels.

This solver simplifies the solve as you can interactively provide updates to what the nuts are and it can backtrack if needed.

## Use

1. Create an `entry.json` file in root folder

    - It needs to be an array of arrays
    - High level array is a board
    - Lower level arrays are poles with nuts
    - Each nut is a string representing color (literal `X` if unknown)
    - lower array index == lower nut

2. Run `main.py` in terminal using command `python main.py`
3. See the list of steps to win the level!

## TODOs

- take into consideration that once revealed, a color will be always grabbed after backtrack even if, when played from scratch, it wouldn't due to being unknown - non-issue for now
- recognize preferred move, maybe?
- justify steps text in STDOUT
