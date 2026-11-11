package cache

import (
	"testing"
	"time"
)

func TestSetGet(t *testing.T) {
	clk := NewFakeClock(time.Unix(1000, 0))
	c := New(2, time.Minute, clk)
	c.Set("a", 1)
	if v, ok := c.Get("a"); !ok || v != 1 {
		t.Fatalf("Get(a) = %v, %v", v, ok)
	}
	if _, ok := c.Get("b"); ok {
		t.Fatal("Get(b) should miss")
	}
}
