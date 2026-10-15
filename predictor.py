import math

def poisson_pmf(k: int, lam: float) -> float:
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)

def poisson_probabilities(home_team, away_team, lambda_home, lambda_away, max_goals=10):
    home = [poisson_pmf(i, lambda_home) for i in range(max_goals + 1)]
    away = [poisson_pmf(i, lambda_away) for i in range(max_goals + 1)]
    total = sum(home) * sum(away)
    home_win = draw = away_win = over15 = over25 = over35 = btts = 0.0
    home_over05 = away_over05 = 0.0
    score_probs = []

    for h, ph in enumerate(home):
        for a, pa in enumerate(away):
            p = ph * pa
            if h > a:
                home_win += p
            elif h == a:
                draw += p
            else:
                away_win += p
            if h + a >= 2:
                over15 += p
            if h + a >= 3:
                over25 += p
            if h + a >= 4:
                over35 += p
            if h >= 1 and a >= 1:
                btts += p
            if h >= 1:
                home_over05 += p
            if a >= 1:
                away_over05 += p
            score_probs.append((p, h, a))

    # Renormalize because only 0..max_goals are included.
    score_probs.sort(reverse=True)
    return {
        "home_win": home_win / total,
        "draw": draw / total,
        "away_win": away_win / total,
        "over_1_5": over15 / total,
        "over_2_5": over25 / total,
        "over_3_5": over35 / total,
        "btts_yes": btts / total,
        "btts_no": 1 - btts / total,
        "home_over_0_5": home_over05 / total,
        "away_over_0_5": away_over05 / total,
        "most_likely_score": f"{score_probs[0][1]}-{score_probs[0][2]}",
    }

def predict_match(home_team, away_team, home_goals_for, home_goals_against,
                  away_goals_for, away_goals_against):
    # Simple baseline: average each team's scoring rate with opponent's conceding rate.
    # These inputs should eventually be estimated from historical data, not guessed.
    lambda_home = max(0.15, (home_goals_for + away_goals_against) / 2)
    lambda_away = max(0.15, (away_goals_for + home_goals_against) / 2)
    return poisson_probabilities(home_team, away_team, lambda_home, lambda_away)
