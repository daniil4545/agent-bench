package cache

import (
	"sync"
	"time"
)

// Clock is the time source of a Cache.
type Clock interface {
	Now() time.Time
}

// SystemClock reads the real time.
type SystemClock struct{}

// Now returns the current time.
func (SystemClock) Now() time.Time { return time.Now() }

// FakeClock is a manually advanced clock for tests. It is safe for concurrent use.
type FakeClock struct {
	mu  sync.Mutex
	now time.Time
}

// NewFakeClock returns a FakeClock set to start.
func NewFakeClock(start time.Time) *FakeClock { return &FakeClock{now: start} }

// Now returns the fake time.
func (c *FakeClock) Now() time.Time {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.now
}

// Advance moves the fake time forward by d.
func (c *FakeClock) Advance(d time.Duration) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.now = c.now.Add(d)
}
