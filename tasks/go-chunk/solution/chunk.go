// Package chunk splits slices into fixed-size pieces.
package chunk

// Split cuts items into consecutive chunks of at most size elements.
func Split(items []int, size int) [][]int {
	if size <= 0 {
		return nil
	}
	var out [][]int
	for i := 0; i < len(items); i += size {
		end := min(i+size, len(items))
		part := make([]int, end-i)
		copy(part, items[i:end])
		out = append(out, part)
	}
	return out
}
