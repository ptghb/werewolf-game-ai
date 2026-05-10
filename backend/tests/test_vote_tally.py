from app.game.vote import tally_votes, VoteResult


def test_majority_winner():
    votes = {"v1": "a", "v2": "a", "v3": "b"}
    r = tally_votes(votes)
    assert r.kind == "winner"
    assert r.winner == "a"
    assert r.tied_candidates == []


def test_abstain_excluded():
    votes = {"v1": "a", "v2": None, "v3": "a"}
    r = tally_votes(votes)
    assert r.kind == "winner"
    assert r.winner == "a"


def test_tie_two_candidates():
    votes = {"v1": "a", "v2": "b", "v3": "a", "v4": "b"}
    r = tally_votes(votes)
    assert r.kind == "tie"
    assert set(r.tied_candidates) == {"a", "b"}


def test_all_abstain():
    votes = {"v1": None, "v2": None}
    r = tally_votes(votes)
    assert r.kind == "no_vote"


def test_empty():
    r = tally_votes({})
    assert r.kind == "no_vote"
