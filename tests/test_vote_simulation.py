from s_expression.vote_simulation import VotingSimulation  # Replace with the correct import path


def test_generate_votes_length():
    """
    Test that the number of generated votes matches the number of voters and each vote has the correct number of candidates.
    """
    sim = VotingSimulation(num_voters=10, num_candidates=5)
    assert len(sim.votes) == 10
    for vote in sim.votes:
        assert len(vote) == 5


def test_fptp_winner():
    """
    Test that the First-Past-The-Post (FPTP) method returns a valid candidate index.
    """
    sim = VotingSimulation(num_voters=10, num_candidates=5)
    winner = sim.fptp()
    assert 0 <= winner < sim.num_candidates


def test_irv_winner():
    """
    Test that the Instant-Runoff Voting (IRV) method returns a valid candidate index.
    """
    sim = VotingSimulation(num_voters=10, num_candidates=5)
    winner = sim.irv()
    assert 0 <= winner < sim.num_candidates


def test_irv_no_elimination_case():
    """
    Test IRV with a scenario where no elimination is needed (one candidate gets >50% of votes initially).
    """
    sim = VotingSimulation(num_voters=5, num_candidates=3)
    sim.votes = [
        [0, 1, 2],
        [0, 2, 1],
        [0, 1, 2],
        [1, 0, 2],
        [2, 1, 0],
    ]
    winner = sim.irv()
    assert winner == 0


def test_irv_elimination_case():
    """
    Test IRV with a scenario where candidates must be eliminated.
    """
    sim = VotingSimulation(num_voters=6, num_candidates=3)
    sim.votes = [
        [0, 1, 2],
        [1, 0, 2],
        [1, 2, 0],
        [2, 1, 0],
        [2, 0, 1],
        [2, 0, 1],
    ]
    winner = sim.irv()
    assert winner == 2


def test_irv_tie_case():
    """
    Test IRV with a tie scenario to ensure the function handles ties correctly.
    """
    sim = VotingSimulation(num_voters=4, num_candidates=2)
    sim.votes = [
        [0, 1],
        [1, 0],
        [0, 1],
        [1, 0],
    ]
    winner = sim.irv()
    assert winner in [0, 1]
