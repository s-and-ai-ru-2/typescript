// Approach 2: flat roll array — scores by scanning rolls at the end.
// This is a complete alternative kept for comparison; the learner stub is unchanged.
export class Bowling {
  private rolls: number[] = []

  public roll(pins: number): void {
    this.rolls.push(pins)
  }

  public score(): number {
    let total = 0
    let i = 0
    for (let frame = 0; frame < 10; frame++) {
      if (this.rolls[i] === 10) {
        // strike: count this roll + next two
        total += 10 + (this.rolls[i + 1] ?? 0) + (this.rolls[i + 2] ?? 0)
        i += 1
      } else if ((this.rolls[i] ?? 0) + (this.rolls[i + 1] ?? 0) === 10) {
        // spare: count 10 + next roll
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
