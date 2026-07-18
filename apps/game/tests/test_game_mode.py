from apps.game.domain.game_mode import ClassicGameModeStrategy


def test_not_over_while_levels_remain():
    mode = ClassicGameModeStrategy()
    assert mode.is_game_over(current_level_index=2, total_levels=5) is False


def test_over_when_all_levels_played():
    mode = ClassicGameModeStrategy()
    assert mode.is_game_over(current_level_index=5, total_levels=5) is True


def test_over_when_past_all_levels():
    mode = ClassicGameModeStrategy()
    assert mode.is_game_over(current_level_index=6, total_levels=5) is True
