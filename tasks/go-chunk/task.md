Bug report: `chunk.Split` loses data.

`Split(items []int, size int) [][]int` should cut `items` into consecutive chunks of at most
`size` elements. When `len(items)` is not a multiple of `size`, the last partial chunk is missing
from the result, so `Split([]int{1,2,3,4,5}, 2)` returns `[[1 2] [3 4]]` instead of
`[[1 2] [3 4] [5]]`. Also, `Split` panics when `size` is 0 or negative: it should return `nil`.

Fix the bug in the package and add a regression test. `go test ./...` must pass.
Chunks must not share memory with a caller who later modifies `items`.
