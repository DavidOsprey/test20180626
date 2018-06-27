@echo off

echo -- UNIT TESTS --
python -m unittest -v myunittest
echo ------------------------------------------------

echo -- SIMULATED RUN --
main.py --cameras="1,2,3,4,5,6,7,8,9,10" --simulate=true
echo ------------------------------------------------

echo -- LIVE RUN --
main.py --timeout=16 --cameras="1,2,3,4,5"
echo ------------------------------------------------