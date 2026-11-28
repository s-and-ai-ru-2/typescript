# Hints

## Approaches

### Approach 1 — Stateful frame tracking (reference)

The reference uses a `Frame` union type (`'X' | 'S' | number | undefined`) to tag each frame as a strike, spare, or open frame. It maintains two parallel arrays — `frames[]` for frame type and `frameScores[]` for scores — and applies bonus scores **retroactively** as future rolls arrive. When a spare bonus arrives it looks back at `frames[currentFrame - 2]`; for a strike bonus it looks back two frames. Validation runs on every `roll()` call.

**When it is clearer**: when you need mid-game validation and per-frame state at any point during a game.  
**Extra work**: O(1) extra memory per roll; slightly complex retroactive bonus logic.

### Approach 2 — Flat roll array (alternative)

Store all rolls in a plain `number[]` and compute the score in one forward pass over 10 frames when `score()` is called. No bonus tracking happens during rolling.

```typescript
// Alternative sketch — not a complete validated solution
class BowlingAlt {
  private rolls: number[] = []

  roll(pins: number): void {
    this.rolls.push(pins)
  }

  score(): number {
    let total = 0
    let i = 0
    for (let frame = 0; frame < 10; frame++) {
      if (this.rolls[i] === 10) {                                           // strike
        total += 10 + (this.rolls[i + 1] ?? 0) + (this.rolls[i + 2] ?? 0)
        i += 1
      } else if ((this.rolls[i] ?? 0) + (this.rolls[i + 1] ?? 0) === 10) { // spare
        total += 10 + (this.rolls[i + 2] ?? 0)
        i += 2
      } else {
        total += (this.rolls[i] ?? 0) + (this.rolls[i + 1] ?? 0)
        i += 2
      }
    }
    return total
  }
}
```

**When it is clearer**: the scoring formula maps directly to the loop — easier to read and reason about.  
**Extra work**: stores all rolls (up to 21 numbers); adding full mid-game validation requires extra index bookkeeping.

## Worked examples

### should be able to score a game with all zeros
20 rolls of `0`. No strikes, no spares. Every frame = 0 + 0 = 0.  
**Total = 0**

### should be able to score a game with no strikes or spares
Rolls: `[3, 6]` × 10 frames. Each frame = 9. 9 × 10 = **90**

### a spare followed by zeros is worth ten points
Rolls: `[6, 4, 0, 0, 0, … 0]`  
Frame 1: 6 + 4 = spare → 10 + next roll (0) = **10**  
Frames 2–10: 0 + 0 = 0 each  
**Total = 10**  
The spare rule: the frame scores 10 plus the very next roll as a bonus. Here that bonus roll is 0, so the spare is worth exactly 10.
