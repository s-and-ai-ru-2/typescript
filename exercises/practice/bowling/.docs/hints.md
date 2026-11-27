# Hints

## Approaches

There are two natural ways to implement bowling scoring in TypeScript.

### Approach 1 — Stateful frame tracking (reference)

The reference implementation tags each frame as `'X'` (strike), `'S'` (spare), or a number, and applies bonus scores retroactively as future rolls arrive. It maintains a `frames[]` array and a parallel `frameScores[]` array. When a spare bonus arrives, it looks back at `frames[currentFrame - 2]`; when a strike bonus arrives, it looks back two frames. Validation (negative pins, too many pins, rolling after game over) runs on every `roll()` call.

**Trade-off**: Handles mid-game state and validation cleanly, but the retroactive bonus logic and frame-tagging make the control flow non-trivial.

### Approach 2 — Flat roll array

An alternative stores every roll in a plain array and computes the score in a single pass over 10 frames when `score()` is called. No bonus tracking happens during rolling.

```typescript
// Sketch — not a complete, validated solution
class BowlingAlt {
  private rolls: number[] = []

  roll(pins: number): void {
    this.rolls.push(pins)
  }

  score(): number {
    let total = 0
    let i = 0
    for (let frame = 0; frame < 10; frame++) {
      if (this.rolls[i] === 10) {           // strike
        total += 10 + this.rolls[i + 1] + this.rolls[i + 2]
        i += 1
      } else if (this.rolls[i] + this.rolls[i + 1] === 10) {  // spare
        total += 10 + this.rolls[i + 2]
        i += 2
      } else {
        total += this.rolls[i] + this.rolls[i + 1]
        i += 2
      }
    }
    return total
  }
}
```

**Trade-off**: The pass-at-the-end approach is simpler to read and reason about, but adding full validation (negative pins, too many pins, 10th-frame extras) requires careful index tracking. It also uses O(n) memory for all rolls rather than a fixed 10-frame array.

### Which to choose

Use the flat roll array when you want clarity about the scoring formula. Use stateful frame tracking when you need real-time validation or in-game state (e.g. a UI that reports per-frame scores as you bowl).

## Worked examples for the named test cases

### should be able to score a game with all zeros

20 rolls of 0. No strikes, no spares. Each frame scores 0 + 0 = 0. Total = **0**.

### should be able to score a game with no strikes or spares

Rolls: `[3, 6]` × 10 frames. Each frame = 9. Total = 9 × 10 = **90**.

### a spare followed by zeros is worth ten points

Rolls: `[6, 4, 0, 0, 0, …]`

Frame 1: 6 + 4 = spare → score = 10 + next roll (0) = **10**  
Frames 2–10: 0 + 0 = 0 each  
Total = **10**

The key rule: a spare counts the _next_ roll as a bonus, added onto the frame's 10. Here the next roll is 0, so the spare is worth exactly 10.
