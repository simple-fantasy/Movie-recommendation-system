"""Auto-seed sample data when the database is empty."""

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
