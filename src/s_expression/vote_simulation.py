from typing import List
import random


# Define a class for the Voting Simulation
class VotingSimulation:
    def __init__(self, num_voters: int, num_candidates: int):
        self.num_voters = num_voters
        self.num_candidates = num_candidates
        self.votes = self.generate_votes()

    def generate_votes(self) -> List[List[int]]:
        # Randomly generate voter preferences
        votes = []
        for _ in range(self.num_voters):
            vote = random.sample(range(self.num_candidates), self.num_candidates)
            votes.append(vote)
        return votes

    def fptp(self) -> int:
        # First-Past-The-Post
        tally = [0] * self.num_candidates
        for vote in self.votes:
            tally[vote[0]] += 1
        return tally.index(max(tally))

    def irv(self) -> int:
        # Instant-Runoff Voting
        remaining_candidates = list(range(self.num_candidates))
        votes = [vote[:] for vote in self.votes]  # Make a copy of the votes

        while True:
            tally = [0] * self.num_candidates
            for vote in votes:
                # Count the top choice for each voter (who hasn't been eliminated)
                for candidate in vote:
                    if candidate in remaining_candidates:
                        tally[candidate] += 1
                        break

            max_votes = max(tally)
            if max_votes > len(votes) / 2:
                return tally.index(max_votes)

            # Find the candidate with the fewest votes
            min_votes = min(tally[candidate] for candidate in remaining_candidates)
            min_candidate = next(
                candidate
                for candidate in remaining_candidates
                if tally[candidate] == min_votes
            )

            # Eliminate the candidate with the fewest votes
            remaining_candidates.remove(min_candidate)

            # Update votes to reflect the removal of the eliminated candidate
            for vote in votes:
                vote[:] = [
                    candidate for candidate in vote if candidate in remaining_candidates
                ]

    # Additional methods for TRS, Borda Count, Approval Voting, etc.


# Example Usage
sim = VotingSimulation(num_voters=100, num_candidates=5)
print("FPTP Winner:", sim.fptp())
print("IRV Winner:", sim.irv())
