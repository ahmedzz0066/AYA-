# Cycle time is a design parameter. Keep these fast.
CSV ?= data/XAUUSD_M5.csv

.PHONY: test smoke backtest walkforward costcurve signals data clean

test:                 ## the only target that must always pass
	python3 -m unittest discover -s tests -v

smoke:                ## end-to-end on synthetic bars (plumbing only, no edge)
	python3 -m xauusd.cli backtest --synthetic 40000

backtest:             ## make backtest CSV=path/to/your.csv
	python3 -m xauusd.cli backtest --csv $(CSV) --trades-csv blotter.csv

walkforward:          ## the only result worth believing
	python3 -m xauusd.cli walkforward --csv $(CSV)

costcurve:            ## does the edge survive a wider spread?
	python3 -m xauusd.cli costcurve --csv $(CSV)

signals:              ## what the live system would have ordered
	python3 -m xauusd.cli signals --csv $(CSV) --last 25

data:
	python3 -m xauusd.cli makedata --bars 60000 --out data/SYNTHETIC_M5.csv

clean:
	rm -rf xauusd/__pycache__ tests/__pycache__ blotter.csv
