#!/bin/bash
set -e
mkdir -p logs
python3 build_qcew_panel_2015_2026.py
python3 port_analysis.py
python3 print_results.py > logs/print_results.txt
python3 make_fig1.py
python3 robust.py 44-45 300 noAK
python3 robust.py 44-45 300
python3 robust.py 44-45 300 noAK lam=10
python3 robust.py 44-45 300 noAK lam=25
python3 robust.py 31-33 300 noAK
python3 robust.py 72 300 noAK
python3 flow.py 44-45 ca 300 noAK
python3 flow.py 72 ca 300 noAK
python3 flow.py 31-33 ca 300 noAK
python3 flow.py 44-45 mx 300
python3 flow.py 72 mx 300
python3 flow.py 44-45 ca 300 noAK detrend
python3 flow.py 72 ca 300 noAK detrend
python3 flow.py 31-33 ca 300 noAK detrend
python3 flow.py 44-45 mx 300 detrend
python3 ci.py 44-45 ca 200 noAK detrend
python3 ci.py 44-45 ca 200 noAK
python3 ci.py 72 ca 200 noAK detrend
python3 ci.py 44-45 mx 200 detrend
python3 make_package.py
