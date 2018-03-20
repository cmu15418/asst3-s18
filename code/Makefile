DEBUG=0
CC=gcc
MPICC = mpicc
OMP=-fopenmp -DOMP
MPI=-DMPI
CFLAGS=-g -O3 -Wall -DDEBUG=$(DEBUG)
LDFLAGS= -lm
DDIR = ./data

CFILES = crun.c graph.c simutil.c sim.c rutil.c cycletimer.c
HFILES = crun.h rutil.h cycletimer.h

GFILES = gengraph.py grun.py rutil.py sim.py viz.py  regress.py benchmark.py grade.py


all: crun crun-omp

crun: crun-seq
	cp -p crun-seq crun

crun-seq: $(CFILES) $(HFILES) $(XFILES)
	$(CC) $(CFLAGS) -o crun-seq $(CFILES) $(LDFLAGS)

crun-omp: $(CFILES) $(HFILES)
	$(CC) $(CFLAGS) $(OMP) -o crun-omp $(CFILES) $(LDFLAGS)
	$(CC) $(CFLAGS) $(OMP) -S -o sim-omp.s sim.c


demo1: grun.py
	@echo "Running Python simulator with text visualization.  Synchronous mode."
	./grun.py -g data/g-u64.gph -r data/r-64-r5.rats -n 20 -u s -v a -p 0.3

demo2: grun.py
	@echo "Running Python simulator with heat-map visualization.  Synchronous mode"
	@echo "Note the oscillatory behavior"
	./grun.py -g data/g-u64.gph -r data/r-64-r5.rats -u s -n 20 -v h -p 0.3

demo3: grun.py
	@echo "Running Python simulator with heat-map visualization.  Rat-order mode"
	@echo "Note the smooth transitions"
	./grun.py -g data/g-u64.gph -r data/r-64-r5.rats -u r -n 20 -v h -p 0.3

demo4: grun.py
	@echo "Running Python simulator with heat-map visualization.  Batch mode"
	@echo "Note the smooth transitions"
	./grun.py -g data/g-u64.gph -r data/r-64-r5.rats -u b -n 20 -v h -p 0.3

demo5: crun grun.py
	@echo "Running C simulator using Python simulator as visualizer"
	./crun -g data/g-u64.gph -r data/r-64-r5.rats -u b -n 20 | ./grun.py -d -v h -p 0.3

demo6: crun grun.py
	@echo "Running on a 160x160 grid graph"
	@echo "This will run a lot faster once you speed up your code"
	./crun -g data/g-u25600.gph -r data/r-25600-r40.rats -u b -n 100 | ./grun.py -d -v h -p 0.02

demo7: crun grun.py
	@echo "Running on a 160x160 tiled graph"
	./crun -g data/g-t25600.gph -r data/r-25600-r40.rats -u b -n 100 | ./grun.py -d -v h -p 0.02

demo8: crun grun.py
	@echo "Running on a 160x160 fractal graph"
	./crun -g data/g-f25600.gph -r data/r-25600-r40.rats -u b -n 100 | ./grun.py -d -v h -p 0.02

demo9: crun grun.py
	@echo "Running on a 160x160 fractal graph, with rats initially along diagonal"
	./crun -g data/g-f25600.gph -r data/r-25600-d40.rats -u b -n 100 | ./grun.py -d -v h -p 0.02

demo10: crun grun.py
	@echo "Running on a 160x160 fractal graph, with rats initially distributed uniformly"
	./crun -g data/g-u25600.gph -r data/r-25600-u40.rats -u b -n 100 | ./grun.py -d -v h -p 0.02

clean:
	rm -f *~ *.pyc
	rm -rf *.dSYM
	rm -f *.tgz
	rm -f crun crun-seq crun-omp
