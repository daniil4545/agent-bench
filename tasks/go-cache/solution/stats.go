package cache

// Stats counts what happened to a Cache since it was created.
type Stats struct {
	Hits        int // Get calls that returned a live entry
	Misses      int // Get calls that found nothing live, expired entries included
	Evictions   int // live entries removed to make room for a new key
	Expirations int // expired entries removed, by Get or by any other method
}
