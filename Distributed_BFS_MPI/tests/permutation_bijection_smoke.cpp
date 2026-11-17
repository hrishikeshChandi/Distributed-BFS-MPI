// Compile with: g++ -O2 -std=c++17 -I mpi_stub tests/permutation_bijection_smoke.cpp -o build/permutation_bijection_smoke
// This unit smoke test includes the implementation to exercise its static permute().
#define main distributed_bfs_program_main
#include "../src/distributed_bfs.cpp"
#undef main

int main() {
  const u64 sizes[] = {2, 3, 5, 7, 10, 31, 32, 33, 41, 255, 256, 257,
                       1024, 1025, 8193, 65536, 875713, 1965206, 2097152};
  for (u64 n : sizes) {
    std::vector<unsigned char> seen(static_cast<size_t>(n), 0);
    for (u64 x = 0; x < n; ++x) {
      const u64 y = permute(x, n, 0xBADC0FFEE0DDF00DULL);
      if (y >= n || seen[static_cast<size_t>(y)]) {
        std::cerr << "Permutation collision/out-of-range: N=" << n
                  << " x=" << x << " y=" << y << "\n";
        return 1;
      }
      seen[static_cast<size_t>(y)] = 1;
    }
  }
  std::cout << "Feistel cycle-walking bijection smoke test: PASS\n";
  return 0;
}
