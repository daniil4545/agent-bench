// Package chunk splits slices into fixed-size pieces.
package chunk

// Split cuts items into consecutive chunks of at most size elements.
func Split(items []int, size int) [][]int {
	var out [][]int
	for i := 0; i+size <= len(items); i += size {
		part := make([]int, size)
		copy(part, items[i:i+size])
		out = append(out, part)
	}
	return out
}
