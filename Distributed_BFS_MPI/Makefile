.PHONY: build smoke test-permutation clean
build:
	./scripts/build.sh
smoke:
	./scripts/build_serial_smoke.sh
test-permutation:
	mkdir -p build
	g++ -O2 -std=c++17 -I mpi_stub tests/permutation_bijection_smoke.cpp -o build/permutation_bijection_smoke
	./build/permutation_bijection_smoke
clean:
	rm -rf build results
