package cache

import (
	"fmt"
	"sync"
	"testing"
	"time"
)

var t0 = time.Unix(1_000_000, 0)

func newTest(capacity int) (*Cache, *FakeClock) {
	clk := NewFakeClock(t0)
	return New(capacity, 10*time.Second, clk), clk
}

func TestHiddenExpiryBoundaryIsInclusive(t *testing.T) {
	c, clk := newTest(4)
	c.Set("a", 1)
	clk.Advance(10*time.Second - time.Nanosecond)
	if _, ok := c.Get("a"); !ok {
		t.Fatal("entry must be live just before expiry")
	}
	clk.Advance(time.Nanosecond)
	if _, ok := c.Get("a"); ok {
		t.Fatal("entry must be expired when now equals expiry")
	}
	s := c.Stats()
	if s.Hits != 1 || s.Misses != 1 || s.Expirations != 1 {
		t.Fatalf("stats = %+v", s)
	}
}

func TestHiddenGetRefreshesRecency(t *testing.T) {
	c, _ := newTest(2)
	c.Set("a", 1)
	c.Set("b", 2)
	c.Get("a")
	c.Set("c", 3)
	if _, ok := c.Get("b"); ok {
		t.Fatal("b was least recently used and must be evicted")
	}
	if _, ok := c.Get("a"); !ok {
		t.Fatal("a was used recently and must stay")
	}
	if got := c.Stats().Evictions; got != 1 {
		t.Fatalf("evictions = %d", got)
	}
}

func TestHiddenSetExistingKey(t *testing.T) {
	c, clk := newTest(2)
	c.Set("a", 1)
	c.Set("b", 2)
	clk.Advance(6 * time.Second)
	c.Set("a", 10) // new value, ttl restarts, a is most recent
	clk.Advance(6 * time.Second)
	if v, ok := c.Get("a"); !ok || v != 10 {
		t.Fatalf("Get(a) = %v, %v", v, ok)
	}
	if _, ok := c.Get("b"); ok {
		t.Fatal("b should have expired")
	}
	if c.Len() != 1 {
		t.Fatalf("Len = %d", c.Len())
	}
	if c.Stats().Evictions != 0 {
		t.Fatal("overwriting a key must not evict")
	}
}

func TestHiddenSetExistingKeyIsMostRecent(t *testing.T) {
	c, _ := newTest(2)
	c.Set("a", 1)
	c.Set("b", 2)
	c.Set("a", 3)
	c.Set("c", 4)
	if _, ok := c.Get("b"); ok {
		t.Fatal("b must be evicted, a was set more recently")
	}
}

func TestHiddenLenIgnoresExpired(t *testing.T) {
	c, clk := newTest(4)
	c.Set("a", 1)
	clk.Advance(5 * time.Second)
	c.Set("b", 2)
	clk.Advance(5 * time.Second)
	if got := c.Len(); got != 1 {
		t.Fatalf("Len = %d, want 1", got)
	}
	if got := c.Stats().Expirations; got != 1 {
		t.Fatalf("expirations = %d", got)
	}
}

func TestHiddenDelete(t *testing.T) {
	c, clk := newTest(4)
	c.Set("a", 1)
	c.Set("b", 2)
	if !c.Delete("a") {
		t.Fatal("Delete of live entry must report true")
	}
	if c.Delete("a") {
		t.Fatal("Delete of missing entry must report false")
	}
	clk.Advance(10 * time.Second)
	if c.Delete("b") {
		t.Fatal("Delete of expired entry must report false")
	}
	if got := c.Stats().Expirations; got != 1 {
		t.Fatalf("expirations = %d", got)
	}
	if c.Len() != 0 {
		t.Fatal("cache must be empty")
	}
}

func TestHiddenEvictingExpiredCountsAsExpiration(t *testing.T) {
	c, clk := newTest(2)
	c.Set("a", 1)
	clk.Advance(10 * time.Second)
	c.Set("b", 2)
	c.Set("c", 3)
	s := c.Stats()
	if s.Expirations != 1 || s.Evictions != 0 {
		t.Fatalf("stats = %+v", s)
	}
}

func TestHiddenConcurrent(t *testing.T) {
	c, clk := newTest(64)
	var wg sync.WaitGroup
	for g := 0; g < 8; g++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for i := 0; i < 500; i++ {
				k := fmt.Sprintf("k%d", (g*31+i)%100)
				c.Set(k, i)
				c.Get(k)
				c.Len()
				c.Stats()
				if i%50 == 0 {
					clk.Advance(time.Second)
				}
				c.Delete(k)
			}
		}()
	}
	wg.Wait()
	if c.Len() > 64 {
		t.Fatalf("Len = %d exceeds capacity", c.Len())
	}
}

func TestHiddenCapacityNeverExceeded(t *testing.T) {
	c, _ := newTest(3)
	for i := 0; i < 20; i++ {
		c.Set(fmt.Sprintf("k%d", i), i)
		c.Set("k0", 0)
		if c.Len() > 3 {
			t.Fatalf("Len = %d", c.Len())
		}
	}
}
