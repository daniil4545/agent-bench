package chunk

import (
	"reflect"
	"testing"
	"time"
)

// splitOrFail calls Split but gives up after a short time, so a looping
// implementation fails the test instead of exhausting memory.
func splitOrFail(t *testing.T, items []int, size int) [][]int {
	t.Helper()
	done := make(chan [][]int, 1)
	go func() { done <- Split(items, size) }()
	select {
	case got := <-done:
		return got
	case <-time.After(300 * time.Millisecond):
		t.Fatalf("Split(%v, %d) does not return", items, size)
		return nil
	}
}

func TestHiddenSplit(t *testing.T) {
	cases := []struct {
		name  string
		items []int
		size  int
		want  [][]int
	}{
		{"exact", []int{1, 2, 3, 4}, 2, [][]int{{1, 2}, {3, 4}}},
		{"remainder", []int{1, 2, 3, 4, 5}, 2, [][]int{{1, 2}, {3, 4}, {5}}},
		{"shorter than size", []int{1, 2}, 5, [][]int{{1, 2}}},
		{"size one", []int{1, 2, 3}, 1, [][]int{{1}, {2}, {3}}},
		{"empty", nil, 3, nil},
		{"zero size", []int{1, 2}, 0, nil},
		{"negative size", []int{1, 2}, -1, nil},
	}
	for _, c := range cases {
		got := splitOrFail(t, c.items, c.size)
		if len(got) == 0 && len(c.want) == 0 {
			continue
		}
		if !reflect.DeepEqual(got, c.want) {
			t.Errorf("%s: got %v, want %v", c.name, got, c.want)
		}
	}
}

func TestHiddenNoSharedMemory(t *testing.T) {
	items := []int{1, 2, 3}
	got := Split(items, 2)
	items[2] = 99
	items[0] = 99
	if got[0][0] != 1 || got[1][0] != 3 {
		t.Fatalf("chunks share memory with input: %v", got)
	}
}
