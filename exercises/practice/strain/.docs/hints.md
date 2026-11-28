# Hints

## Contract cases walkthrough

The `keep` function filters an array using a predicate. Three edge cases show how the contract handles boundaries.

### Decision table

| Input array | Predicate | Operation | Expected output | Why |
|-------------|-----------|-----------|-----------------|-----|
| `[]` | `(_) => true` | `keep` | `[]` | No elements to test; empty in, empty out |
| `[1, 3, 5]` | `(_) => true` | `keep` | `[1, 3, 5]` | Every element passes; all are kept |
| `[1, 3, 5]` | `(_) => false` | `keep` | `[]` | No element passes; none are kept |

### Case 1: keeps on empty array returns empty array

```typescript
keep<number>([], (_) => true)  // → []
```

The predicate is never called because there are no elements. The result is always `[]` regardless of the predicate. This is the base case.

### Case 2: keeps everything

```typescript
keep<number>([1, 3, 5], (_) => true)  // → [1, 3, 5]
```

Every element passes the predicate. The output preserves all elements in their original order.

### Case 3: keeps nothing

```typescript
keep<number>([1, 3, 5], (_) => false)  // → []
```

No element passes. The result is `[]` — not `undefined`, not `null`. The contract requires an empty array when nothing qualifies.

### TypeScript representation

The generic type parameter `T` means `keep` works on any array type:

```typescript
keep<number>([1, 3, 5], (n) => n > 2)   // → [3, 5]
keep<string>(['a', 'b'], (s) => s === 'a') // → ['a']
```

### What the exercise leaves unspecified

- The predicate receives only the element value, not its index
- The exercise does not forbid mutating the input array, but the reference does not mutate it
- No ordering requirement beyond preserving input order is specified
