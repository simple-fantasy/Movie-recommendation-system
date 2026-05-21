"""Auto-seed sample data when the database is empty."""


def _seed_watch_links(db, WatchLink, movies):
    """为种子电影添加在线观看链接，返回创建的链接数"""
    watch_link_data = {
        "The Shawshank Redemption": [
            {"platform": "bilibili", "url": "https://search.bilibili.com/all?keyword=肖申克的救赎", "quality": "HD", "is_free": True, "is_official": False},
            {"platform": "YouTube", "url": "https://www.youtube.com/results?search_query=The+Shawshank+Redemption+full+movie", "quality": "HD", "is_free": True, "is_official": False},
        ],
        "The Godfather": [
            {"platform": "bilibili", "url": "https://search.bilibili.com/all?keyword=教父", "quality": "4K", "is_free": False, "is_official": False},
            {"platform": "YouTube", "url": "https://www.youtube.com/results?search_query=The+Godfather+full+movie", "quality": "HD", "is_free": False, "is_official": False},
        ],
        "The Dark Knight": [
            {"platform": "bilibili", "url": "https://search.bilibili.com/all?keyword=蝙蝠侠黑暗骑士", "quality": "4K", "is_free": True, "is_official": False},
            {"platform": "YouTube", "url": "https://www.youtube.com/results?search_query=The+Dark+Knight+full+movie", "quality": "HD", "is_free": False, "is_official": False},
            {"platform": "iQiyi", "url": "https://www.iqiyi.com/search.html?key=蝙蝠侠黑暗骑士", "quality": "4K", "is_free": False, "is_official": False},
        ],
        "Pulp Fiction": [
            {"platform": "bilibili", "url": "https://search.bilibili.com/all?keyword=低俗小说", "quality": "HD", "is_free": True, "is_official": False},
            {"platform": "YouTube", "url": "https://www.youtube.com/results?search_query=Pulp+Fiction+full+movie", "quality": "HD", "is_free": False, "is_official": False},
        ],
        "Forrest Gump": [
            {"platform": "bilibili", "url": "https://search.bilibili.com/all?keyword=阿甘正传", "quality": "4K", "is_free": True, "is_official": False},
            {"platform": "iQiyi", "url": "https://www.iqiyi.com/search.html?key=阿甘正传", "quality": "4K", "is_free": False, "is_official": True},
            {"platform": "YouTube", "url": "https://www.youtube.com/results?search_query=Forrest+Gump+full+movie", "quality": "HD", "is_free": False, "is_official": False},
        ],
        "Inception": [
            {"platform": "bilibili", "url": "https://search.bilibili.com/all?keyword=盗梦空间", "quality": "4K", "is_free": True, "is_official": False},
            {"platform": "iQiyi", "url": "https://www.iqiyi.com/search.html?key=盗梦空间", "quality": "4K", "is_free": False, "is_official": True},
            {"platform": "YouTube", "url": "https://www.youtube.com/results?search_query=Inception+full+movie", "quality": "HD", "is_free": False, "is_official": False},
        ],
        "The Matrix": [
            {"platform": "bilibili", "url": "https://search.bilibili.com/all?keyword=黑客帝国", "quality": "4K", "is_free": True, "is_official": False},
            {"platform": "YouTube", "url": "https://www.youtube.com/results?search_query=The+Matrix+full+movie", "quality": "HD", "is_free": False, "is_official": False},
        ],
        "Interstellar": [
            {"platform": "bilibili", "url": "https://search.bilibili.com/all?keyword=星际穿越", "quality": "4K", "is_free": True, "is_official": False},
            {"platform": "iQiyi", "url": "https://www.iqiyi.com/search.html?key=星际穿越", "quality": "4K", "is_free": False, "is_official": True},
            {"platform": "YouTube", "url": "https://www.youtube.com/results?search_query=Interstellar+full+movie", "quality": "HD", "is_free": False, "is_official": False},
        ],
        "Spirited Away": [
            {"platform": "bilibili", "url": "https://search.bilibili.com/all?keyword=千与千寻", "quality": "4K", "is_free": True, "is_official": False},
            {"platform": "YouTube", "url": "https://www.youtube.com/results?search_query=Spirited+Away+full+movie", "quality": "HD", "is_free": False, "is_official": False},
        ],
        "Coco": [
            {"platform": "bilibili", "url": "https://search.bilibili.com/all?keyword=寻梦环游记", "quality": "4K", "is_free": True, "is_official": False},
            {"platform": "iQiyi", "url": "https://www.iqiyi.com/search.html?key=寻梦环游记", "quality": "4K", "is_free": False, "is_official": True},
        ],
        "Avengers: Endgame": [
            {"platform": "bilibili", "url": "https://search.bilibili.com/all?keyword=复仇者联盟4终局之战", "quality": "4K", "is_free": True, "is_official": False},
            {"platform": "YouTube", "url": "https://www.youtube.com/results?search_query=Avengers+Endgame+full+movie", "quality": "HD", "is_free": False, "is_official": False},
        ],
        "Joker": [
            {"platform": "bilibili", "url": "https://search.bilibili.com/all?keyword=小丑2019", "quality": "4K", "is_free": True, "is_official": False},
            {"platform": "YouTube", "url": "https://www.youtube.com/results?search_query=Joker+2019+full+movie", "quality": "HD", "is_free": False, "is_official": False},
        ],
        "Your Name.": [
            {"platform": "bilibili", "url": "https://search.bilibili.com/all?keyword=你的名字", "quality": "4K", "is_free": True, "is_official": False},
        ],
        "Parasite": [
            {"platform": "bilibili", "url": "https://search.bilibili.com/all?keyword=寄生虫韩国电影", "quality": "4K", "is_free": True, "is_official": False},
            {"platform": "YouTube", "url": "https://www.youtube.com/results?search_query=Parasite+2019+full+movie", "quality": "HD", "is_free": False, "is_official": False},
        ],
        "Fight Club": [
            {"platform": "bilibili", "url": "https://search.bilibili.com/all?keyword=搏击俱乐部", "quality": "HD", "is_free": True, "is_official": False},
        ],
        "Schindler's List": [
            {"platform": "bilibili", "url": "https://search.bilibili.com/all?keyword=辛德勒的名单", "quality": "HD", "is_free": True, "is_official": False},
        ],
        "Goodfellas": [
            {"platform": "bilibili", "url": "https://search.bilibili.com/all?keyword=好家伙电影", "quality": "HD", "is_free": True, "is_official": False},
        ],
        "The Lord of the Rings: The Return of the King": [
            {"platform": "bilibili", "url": "https://search.bilibili.com/all?keyword=指环王3王者归来", "quality": "4K", "is_free": True, "is_official": False},
        ],
        "The Silence of the Lambs": [
            {"platform": "bilibili", "url": "https://search.bilibili.com/all?keyword=沉默的羔羊", "quality": "HD", "is_free": True, "is_official": False},
        ],
        "Whiplash": [
            {"platform": "bilibili", "url": "https://search.bilibili.com/all?keyword=爆裂鼓手", "quality": "HD", "is_free": True, "is_official": False},
        ],
    }

    count = 0
    for movie in movies:
        links = watch_link_data.get(movie.title, [])
        for link_info in links:
            existing = WatchLink.query.filter_by(movie_id=movie.id, url=link_info["url"]).first()
            if existing:
                continue
            link = WatchLink(
                movie_id=movie.id,
                platform=link_info["platform"],
                url=link_info["url"],
                quality=link_info.get("quality", "HD"),
                is_free=link_info.get("is_free", True),
                is_official=link_info.get("is_official", False),
                status="active",
            )
            db.session.add(link)
            count += 1

    if count:
        db.session.commit()
        print(f"[Seed] Created {count} watch links for {len(watch_link_data)} movies")
    return count


def seed_sample_data(db, Movie, User, Rating):
    """Seed sample movies, demo user, and ratings if the DB is empty."""
    if Movie.query.first() is not None:
        return False  # Already seeded

    sample_movies = [
        {"title": "The Shawshank Redemption", "year": 1994, "genres": "Drama", "description": "Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency."},
        {"title": "The Godfather", "year": 1972, "genres": "Crime,Drama", "description": "The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant youngest son."},
        {"title": "The Dark Knight", "year": 2008, "genres": "Action,Crime,Drama", "description": "When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice."},
        {"title": "Pulp Fiction", "year": 1994, "genres": "Crime,Drama", "description": "The lives of two mob hitmen, a boxer, a gangster and his wife, and a pair of diner bandits intertwine in four tales of violence and redemption."},
        {"title": "Schindler's List", "year": 1993, "genres": "Biography,Drama,History", "description": "In German-occupied Poland during World War II, industrialist Oskar Schindler gradually becomes concerned for his Jewish workforce after witnessing their persecution by the Nazis."},
        {"title": "Forrest Gump", "year": 1994, "genres": "Comedy,Drama,Romance", "description": "The presidencies of Kennedy and Johnson, the Vietnam War, the Watergate scandal and other historical events unfold from the perspective of an Alabama man with an IQ of 75."},
        {"title": "Inception", "year": 2010, "genres": "Action,Adventure,Sci-Fi", "description": "A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O."},
        {"title": "The Matrix", "year": 1999, "genres": "Action,Sci-Fi", "description": "When a beautiful stranger leads computer hacker Neo to a forbidding underworld, he discovers the shocking truth -- the life he knows is the elaborate deception of an evil cyber-intelligence."},
        {"title": "Fight Club", "year": 1999, "genres": "Drama", "description": "An insomniac office worker and a devil-may-care soap maker form an underground fight club that evolves into much more."},
        {"title": "Interstellar", "year": 2014, "genres": "Adventure,Drama,Sci-Fi", "description": "A team of explorers travel through a wormhole in space in an attempt to ensure humanity's survival."},
        {"title": "Parasite", "year": 2019, "genres": "Comedy,Drama,Thriller", "description": "Greed and class discrimination threaten the newly formed symbiotic relationship between the wealthy Park family and the destitute Kim clan."},
        {"title": "Spirited Away", "year": 2001, "genres": "Animation,Adventure,Family", "description": "During her family's move to the suburbs, a sullen 10-year-old girl wanders into a world ruled by gods, witches, and spirits, and where humans are changed into beasts."},
        {"title": "The Lord of the Rings: The Return of the King", "year": 2003, "genres": "Action,Adventure,Drama", "description": "Gandalf and Aragorn lead the World of Men against Sauron's army to draw his gaze from Frodo and Sam as they approach Mount Doom with the One Ring."},
        {"title": "Goodfellas", "year": 1990, "genres": "Biography,Crime,Drama", "description": "The story of Henry Hill and his life in the mob, covering his relationship with his wife Karen Hill and his mob partners Jimmy Conway and Tommy DeVito."},
        {"title": "Your Name.", "year": 2016, "genres": "Animation,Drama,Fantasy", "description": "Two strangers find themselves linked in a bizarre way. When a connection forms, will distance be the only thing to keep them apart?"},
        {"title": "Coco", "year": 2017, "genres": "Animation,Adventure,Comedy", "description": "Aspiring musician Miguel enters the Land of the Dead to find his great-great-grandfather, a legendary singer."},
        {"title": "Avengers: Endgame", "year": 2019, "genres": "Action,Adventure,Drama", "description": "After the devastating events of Avengers: Infinity War, the universe is in ruins. With the help of remaining allies, the Avengers assemble once more in order to reverse Thanos' actions and restore balance to the universe."},
        {"title": "Joker", "year": 2019, "genres": "Crime,Drama,Thriller", "description": "In Gotham City, mentally troubled comedian Arthur Fleck is disregarded and mistreated by society. He then embarks on a downward spiral of revolution and bloody crime."},
        {"title": "The Silence of the Lambs", "year": 1991, "genres": "Crime,Drama,Thriller", "description": "A young F.B.I. cadet must receive the help of an incarcerated and manipulative cannibal killer to help catch another serial killer."},
        {"title": "Whiplash", "year": 2014, "genres": "Drama,Music", "description": "A promising young drummer enrolls at a cut-throat music conservatory where his dreams of greatness are mentored by an instructor who will stop at nothing to realize a student's potential."},
    ]

    movies = []
    for m in sample_movies:
        movie = Movie(
            title=m["title"],
            year=m["year"],
            genres=m["genres"],
            description=m["description"],
            avg_rating=0,
            rating_count=0,
        )
        db.session.add(movie)
        movies.append(movie)

    # Create demo user
    demo_user = User(username="demo", is_admin=False, is_active=True)
    demo_user.set_password("demo123")
    db.session.add(demo_user)

    # Create admin user
    admin = User(username="admin", is_admin=True, is_active=True)
    admin.set_password("admin123")
    db.session.add(admin)

    # Add some ratings for demo user so recs work
    import random
    for movie in movies:
        if random.random() < 0.4:  # Rate ~40% of movies
            rating = Rating(
                user_id=None,  # Will be set after flush
                movie_id=None,
                rating=round(random.uniform(2.5, 5.0) * 2) / 2,  # Random 2.5-5.0 in 0.5 steps
            )
            rating.user = demo_user
            rating.movie = movie
            db.session.add(rating)
            movie.rating_count += 1
            movie.avg_rating = rating.rating  # Simplified

    db.session.commit()
    print(f"[Seed] Created {len(movies)} sample movies, demo user (demo/demo123), admin (admin/admin123)")
    return True
