def three_way_temporal_split(ratings_by_user, config):
    train = {}
    val = {}
    test = {}

    for uid, items in ratings_by_user.items():
        if len(items) < config.min_user_interactions:
            continue

        train_items = items[:-5]
        val_item = items[-5]
        test_candidates = items[-3:]

        test_items = [
            (mid, r) for mid, r, _ts in test_candidates if r >= config.like_threshold
        ]
        if not test_items:
            continue

        train[uid] = [(mid, r) for mid, r, _ts in train_items]
        val[uid] = (val_item[0], val_item[1])
        test[uid] = test_items

    return train, val, test
