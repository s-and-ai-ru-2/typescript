# Hints

## TypeScript guidance — const assertion (`as const`)

### The construct in the reference

In `Board.winner()`, the reference uses:

```typescript
const players = ['X', 'O'] as const
```

This is a **const assertion**. Without it, TypeScript infers `string[]` for the array, so each `player` in the for-of loop is typed as `string`. Because `checkWin` is typed as `(player: 'X' | 'O') => boolean`, passing a `string` causes a compile-time error. With `as const`, TypeScript infers `readonly ['X', 'O']`, narrowing each element to the literal union `'X' | 'O'` — exactly what `checkWin` expects.

### Standalone micro-example

```typescript
// Without as const — element type is string
const wide = ['X', 'O']
// wide[0] → type: string

// With as const — element type is 'X' | 'O'
const narrow = ['X', 'O'] as const
// narrow[0] → type: 'X'

function describe(player: 'X' | 'O'): string {
  return player === 'X' ? 'X goes left-to-right' : 'O goes top-to-bottom'
}

// This compiles and returns: 'X goes left-to-right'
describe(narrow[0])

// This would be a compile error:
// describe(wide[0])
// Error: Argument of type 'string' is not assignable to parameter of type '"X" | "O"'
```

**Output of `describe(narrow[0])`**: `'X goes left-to-right'`  
**Output of `describe(narrow[1])`**: `'O goes top-to-bottom'`

### The pitfall

If you write `const players = ['X', 'O']` without `as const` and iterate with `for (const player of players)`, the type of `player` is `string`. Any method in your `Board` implementation that accepts `player: 'X' | 'O'` will reject it at compile time. You would need an explicit cast like `player as 'X' | 'O'` — but that is unsafe. The const assertion is the correct fix.

### Why it matters for this exercise

`Board.checkWin` takes `player: 'X' | 'O'`. The const assertion on the players array is what allows the for-of loop in `winner()` to call `checkWin(player)` without a type error or unsafe cast.

**Reference**: [TypeScript Handbook — const assertions](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#literal-types)
