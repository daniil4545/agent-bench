package chunk

import (
	"reflect"
	"testing"
)

func TestSplitExact(t *testing.T) {
	got := Split([]int{1, 2, 3, 4}, 2)
	want := [][]int{{1, 2}, {3, 4}}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("got %v, want %v", got, want)
	}
}
