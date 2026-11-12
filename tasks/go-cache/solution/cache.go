// Package cache is a small LRU cache with a time-to-live per entry.
package cache

import (
	"container/list"
	"sync"
	"time"
)

type entry struct {
	key     string
	value   any
	expires time.Time
}

// Cache holds at most cap entries. Each entry lives for ttl after it was set.
// A Cache is safe for concurrent use by multiple goroutines.
type Cache struct {
	mu    sync.Mutex
	cap   int
	ttl   time.Duration
	clock Clock
	items map[string]*list.Element
	order *list.List // front is the most recently used entry
	stats Stats
}

// New returns a Cache of the given capacity (at least 1) and time-to-live.
func New(capacity int, ttl time.Duration, clock Clock) *Cache {
	return &Cache{
		cap:   max(capacity, 1),
		ttl:   ttl,
		clock: clock,
		items: make(map[string]*list.Element),
		order: list.New(),
	}
}

func expired(e *entry, now time.Time) bool {
	return !now.Before(e.expires)
}

func (c *Cache) remove(el *list.Element) {
	delete(c.items, el.Value.(*entry).key)
	c.order.Remove(el)
}

// Set stores value under key and makes it the most recently used entry.
// A key has at most one entry: setting it again replaces the value and restarts
// its time-to-live. When the cache is full and key is new, the least recently
// used entry is removed first; that counts as an eviction, unless the entry had
// already expired, which counts as an expiration.
func (c *Cache) Set(key string, value any) {
	c.mu.Lock()
	defer c.mu.Unlock()
	now := c.clock.Now()
	e := &entry{key: key, value: value, expires: now.Add(c.ttl)}
	if el, ok := c.items[key]; ok {
		el.Value = e
		c.order.MoveToFront(el)
		return
	}
	if len(c.items) >= c.cap {
		if back := c.order.Back(); back != nil {
			if expired(back.Value.(*entry), now) {
				c.stats.Expirations++
			} else {
				c.stats.Evictions++
			}
			c.remove(back)
		}
	}
	c.items[key] = c.order.PushFront(e)
}

// Get returns the value stored under key. A live entry is a hit and becomes the
// most recently used entry. An entry is expired once the clock reads its expiry
// time or later; Get removes an expired entry and reports a miss and an expiration.
func (c *Cache) Get(key string) (any, bool) {
	c.mu.Lock()
	defer c.mu.Unlock()
	el, ok := c.items[key]
	if !ok {
		c.stats.Misses++
		return nil, false
	}
	e := el.Value.(*entry)
	if expired(e, c.clock.Now()) {
		c.remove(el)
		c.stats.Misses++
		c.stats.Expirations++
		return nil, false
	}
	c.order.MoveToFront(el)
	c.stats.Hits++
	return e.value, true
}

// Delete removes key and reports whether a live entry was removed. Removing an
// entry that had already expired counts as an expiration and reports false.
func (c *Cache) Delete(key string) bool {
	c.mu.Lock()
	defer c.mu.Unlock()
	el, ok := c.items[key]
	if !ok {
		return false
	}
	live := !expired(el.Value.(*entry), c.clock.Now())
	if !live {
		c.stats.Expirations++
	}
	c.remove(el)
	return live
}

// Len returns the number of live entries. Expired entries are not counted, and
// are removed (counting as expirations).
func (c *Cache) Len() int {
	c.mu.Lock()
	defer c.mu.Unlock()
	now := c.clock.Now()
	for el := c.order.Back(); el != nil; {
		prev := el.Prev()
		if expired(el.Value.(*entry), now) {
			c.remove(el)
			c.stats.Expirations++
		}
		el = prev
	}
	return len(c.items)
}

// Stats returns a snapshot of the counters.
func (c *Cache) Stats() Stats {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.stats
}
