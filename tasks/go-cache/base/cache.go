// Package cache is a small LRU cache with a time-to-live per entry.
package cache

import (
	"container/list"
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

func (c *Cache) expired(e *entry) bool {
	return c.clock.Now().After(e.expires)
}

// Set stores value under key and makes it the most recently used entry.
// A key has at most one entry: setting it again replaces the value and restarts
// its time-to-live. When the cache is full and key is new, the least recently
// used entry is removed first; that counts as an eviction, unless the entry had
// already expired, which counts as an expiration.
func (c *Cache) Set(key string, value any) {
	exp := c.clock.Now().Add(c.ttl)
	if len(c.items) >= c.cap {
		if back := c.order.Back(); back != nil {
			old := back.Value.(*entry)
			delete(c.items, old.key)
			c.order.Remove(back)
			c.stats.Evictions++
		}
	}
	c.items[key] = c.order.PushFront(&entry{key: key, value: value, expires: exp})
}

// Get returns the value stored under key. A live entry is a hit and becomes the
// most recently used entry. An entry is expired once the clock reads its expiry
// time or later; Get removes an expired entry and reports a miss and an expiration.
func (c *Cache) Get(key string) (any, bool) {
	el, ok := c.items[key]
	if !ok {
		c.stats.Misses++
		return nil, false
	}
	e := el.Value.(*entry)
	if c.expired(e) {
		delete(c.items, key)
		c.order.Remove(el)
		c.stats.Misses++
		return nil, false
	}
	c.stats.Hits++
	return e.value, true
}

// Delete removes key and reports whether a live entry was removed. Removing an
// entry that had already expired counts as an expiration and reports false.
func (c *Cache) Delete(key string) bool {
	el, ok := c.items[key]
	if !ok {
		return false
	}
	delete(c.items, key)
	c.order.Remove(el)
	return true
}

// Len returns the number of live entries. Expired entries are not counted, and
// are removed (counting as expirations).
func (c *Cache) Len() int {
	return len(c.items)
}

// Stats returns a snapshot of the counters.
func (c *Cache) Stats() Stats {
	return c.stats
}
