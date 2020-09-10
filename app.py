# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf.csrf import CsrfProtect
from forms import *
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import or_
from sqlalchemy import inspect
# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object("config")
db = SQLAlchemy(app)
migrate = Migrate(app, db)
db.create_all()
csrf = CsrfProtect(app)

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#


artist_genre_association = db.Table('artist_genres',
                                    db.Column('artist_id', db.ForeignKey('Artist.id'), primary_key=True),
                                    db.Column('genre_id', db.ForeignKey('Genre.id'), primary_key=True)
                                    )

venue_genre_association = db.Table('venue_genres',
                                   db.Column('venue_id', db.ForeignKey('Venue.id'), primary_key=True),
                                   db.Column('genre_id', db.ForeignKey('Genre.id'), primary_key=True)
                                   )



class Venue(db.Model):
    __tablename__ = "Venue"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    address = db.Column(db.String(120))
    city_id = db.Column(db.Integer, db.ForeignKey('City.id'), nullable=False)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String)
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String)

    shows = db.relationship('Show', backref="Venue", lazy='dynamic')
    genres = db.relationship('Genre', secondary=venue_genre_association ,backref=db.backref("Venue", lazy=True))

    city = db.relationship('City', backref="City", lazy=True)

    @classmethod
    def get_or_create(cls, session, **kwargs):

        try:
            return session.query(cls).filter_by(**kwargs).one()
        except NoResultFound:
            r = cls(**kwargs)
            session.add(r)

            return r

    @hybrid_property
    def upcoming_shows(self):

        today = datetime.now()

        return self.shows.filter(Show.start_time > today).all()

    @hybrid_property
    def past_shows(self):

        today = datetime.now()

        return self.shows.filter(Show.start_time < today).all()

    @hybrid_property
    def upcoming_shows_count(self):

        return len(self.upcoming_shows)

    @hybrid_property
    def past_shows_count(self):

        return len(self.past_shows)



class Genre(db.Model):

    __tablename__ = "Genre"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)

    @classmethod
    def get_or_create(cls, session, **kwargs):

        try:
            return session.query(cls).filter_by(**kwargs).one()
        except NoResultFound:
            r = cls(**kwargs)
            session.add(r)
            session.commit()

            return r



class Artist(db.Model):
    __tablename__ = "Artist"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey('City.id'), nullable=False)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String)
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String)

    shows = db.relationship('Show', backref='Artist', lazy='dynamic')
    genres = db.relationship('Genre', secondary=artist_genre_association, backref=db.backref('Genre', lazy=True))

    city = db.relationship('City', backref="Artist", lazy=True)

    @classmethod
    def get_or_create(cls, session, **kwargs):

        try:
            return session.query(cls).filter_by(**kwargs).one()
        except NoResultFound:
            r = cls(**kwargs)
            session.add(r)

            return r

    @hybrid_property
    def upcoming_shows(self):

        today = datetime.now()

        return self.shows.filter(Show.start_time > today).all()

    @hybrid_property
    def past_shows(self):

        today = datetime.now()

        return self.shows.filter(Show.start_time < today).all()

    @hybrid_property
    def upcoming_shows_count(self):

        return len(self.upcoming_shows)

    @hybrid_property
    def past_shows_count(self):

        return len(self.past_shows)

class Show(db.Model):
    __tablename__ = "Show"
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)

    @classmethod
    def get_or_create(cls, session, **kwargs):

        try:
            return session.query(cls).filter_by(**kwargs).one()
        except NoResultFound:
            r = cls(**kwargs)
            session.add(r)

            return r


class City(db.Model):

    __tablename__ = "City"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    state_id = db.Column(db.Integer, db.ForeignKey('State.id'), nullable=False)
    state = db.relationship('State', back_populates="cities")

    venues = db.relationship('Venue', backref='City', lazy=True)
    artists = db.relationship('Artist', backref='City', lazy=True)

    @classmethod
    def get_or_create(cls, session, **kwargs):

        try:
            return session.query(cls).filter_by(**kwargs).one()
        except NoResultFound:
            return cls(**kwargs)


class State(db.Model):
    __tablename__ = "State"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)

    cities = db.relationship('City', back_populates="state")

    @classmethod
    def get_or_create(cls, session, **kwargs):

        try:
            return session.query(cls).filter_by(**kwargs).one()
        except NoResultFound:
            return cls(**kwargs)


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format="medium"):
    date = value
    if format == "full":
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == "medium":
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters["datetime"] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route("/")
def index():
    return render_template("pages/home.html")


#  Venues
#  ----------------------------------------------------------------


@app.route("/venues")
def venues():


    return render_template("pages/venues.html", cities=City.query.all())


@app.route("/venues/search", methods=["POST"])
def search_venues():

    query_venue = request.form.get('search_term')

    results = Venue.query.filter(Venue.name.ilike(f"%{query_venue.strip().lower()}%")).all()

    response = {
        "count": len(results),
        "data": results,
    }

    return render_template(
        "pages/search_venues.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/venues/<int:venue_id>", methods=["GET"])
def show_venue(venue_id):

    try:
        result = Venue.query.filter(Venue.id == venue_id).one()
    except:
        result = None


    return render_template("pages/show_venue.html", venue=result)


#  Create Venue
#  ----------------------------------------------------------------


@app.route("/venues/create", methods=["GET"])
@csrf.exempt
def create_venue_form():
    form = VenueForm()
    return render_template("forms/new_venue.html", form=form)


@app.route("/venues/create", methods=["POST"])
def create_venue_submission():

    with db.session.no_autoflush:

        form = VenueForm(request.form)

        if request.method == "POST" and form.validate():
            try:
                venue = Venue.get_or_create(db.session, name=form.name.data)

                venue.city = City.get_or_create(db.session, name=form.city.data, state=State.get_or_create(db.session, name=form.states.data))

                venue.address = form.address.data
                venue.phone = form.phone.data

                venue.genres = [Genre.get_or_create(db.session, name=g) for g in form.genres.data]
                venue.facebook_link = form.facebook_link.data
                venue.image_link = form.image_link.data
                venue.seeking_talent = form.seeking_talent.data
                venue.seeking_description = form.seeking_talent_description.data

                db.session.add(venue)

                db.session.commit()

                db.session.close()
            except:
                flash('An error occurred. Venue '+ form.name.data + ' could not be listed.')
                db.session.rollback()
                db.session.close()
                return redirect(url_for('create_venue_submission'))

        return redirect(url_for('venues'))

@csrf.exempt
@app.route("/venues/<int:venue_id>", methods=['DELETE'])
def delete_venue(venue_id):

    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
    except Exception as e:
        print(f'Error ==> {e}')
        flash('An error occurred. Venue could not be deleted.')
        db.session.rollback()
        abort(400)
    finally:
        db.session.close()

    return "Success"

@csrf.exempt
@app.route("/artists/<int:artist_id>", methods=['DELETE'])
def delete_artist(artist_id):

    try:
        a = Artist.query.get(artist_id)
        db.session.delete(a)
        db.session.commit()
    except Exception as e:
        print(f'Error ==> {e}')
        flash('An error occurred. Artist could not be deleted.')
        db.session.rollback()
        abort(400)
    finally:
        db.session.close()

    return "Success"


#  Artists
#  ----------------------------------------------------------------
@app.route("/artists")
def artists():

    return render_template("pages/artists.html", artists=Artist.query.all())

@csrf.exempt
@app.route("/artists/search", methods=["POST"])
def search_artists():

    try:
        result = Artist.query.filter(Artist.name.ilike(f"%{request.form.get('search_term').strip().lower()}%")).all()
    except:
        result = None

    response = {
        "count": len(result),
        "data": result,
    }

    return render_template(
        "pages/search_artists.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/artists/<int:artist_id>")
def show_artist(artist_id):

    try:
        result = Artist.query.filter(Artist.id == artist_id).one()
    except:
        result = None

    return render_template("pages/show_artist.html", artist=result)


#  Update
#  ----------------------------------------------------------------
@app.route("/artists/<int:artist_id>/edit", methods=["GET"])
def edit_artist(artist_id):
    with db.session.no_autoflush:

        a = Artist.query.filter_by(id=artist_id).one()
        artist = {
            "id": a.id,
            "name": a.name,
            "genres": [g.name for g in a.genres],
            "city": a.city.name,
            "states": a.city.state.name,
            "phone": a.phone,
            "website_link": a.website,
            "facebook_link": a.facebook_link,
            "seeking_venue": a.seeking_venue,
            "seeking_description": a.seeking_description,
            "image_link": a.image_link,
        }
        form = ArtistForm(data=artist)

        return render_template("forms/edit_artist.html", form=form, artist=artist)


@app.route("/artists/<int:artist_id>/edit", methods=["POST"])
def edit_artist_submission(artist_id):
    with db.session.no_autoflush:

        form = ArtistForm(request.form)

        if request.method == "POST" and form.validate():
            try:
                artist = Artist.get_or_create(db.session, name=form.name.data)

                artist.city = City.get_or_create(db.session, name=form.city.data, state=State.get_or_create(db.session, name=form.states.data))

                artist.phone = form.phone.data

                artist.genres = [Genre.get_or_create(db.session, name=g) for g in form.genres.data]
                artist.facebook_link = form.facebook_link.data
                artist.image_link = form.image_link.data
                artist.seeking_venue = form.seeking_venue.data
                artist.seeking_description = form.seeking_description.data
                artist.website = form.website_link.data
                db.session.add(artist)

                db.session.commit()

                db.session.close()
            except Exception as e:
                flash('An error occurred. Artist '+ form.name.data + ' could not be updated.')
                print(e)
                db.session.rollback()
                db.session.close()
                return redirect(url_for('artists'))

        return redirect(url_for("show_artist", artist_id=artist_id))


@app.route("/venues/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):
    with db.session.no_autoflush:

        try:

            venue = Venue.query.filter_by(id=venue_id).one()
            v = {
                "id": venue.id,
                "name": venue.name,
                "city": venue.city.name,
                "states": venue.city.state.name,
                "genres": [g.name for g in venue.genres],
                "phone": venue.phone,
                "address": venue.address,
                "facebook_link": venue.facebook_link,
                "image_link": venue.image_link,
                "seeking_talent": venue.seeking_talent,
                "seeking_talent_description":  venue.seeking_description
            }
            form = VenueForm(data=v)
            return render_template("forms/edit_venue.html", form=form, venue=v)
        except:
            flash('No Venue Found')
            return redirect(url_for('venues'))


@app.route("/venues/<int:venue_id>/edit", methods=["POST"])
def edit_venue_submission(venue_id):
    with db.session.no_autoflush:

        form = VenueForm(request.form)

        if request.method == "POST" and form.validate():
            try:
                venue = Venue.get_or_create(db.session, name=form.name.data)

                venue.city = City.get_or_create(db.session, name=form.city.data, state=State.get_or_create(db.session, name=form.states.data))

                venue.address = form.address.data
                venue.phone = form.phone.data

                venue.genres = [Genre.get_or_create(db.session, name=g) for g in form.genres.data]
                venue.facebook_link = form.facebook_link.data
                venue.image_link = form.image_link.data
                venue.seeking_talent = form.seeking_talent.data
                venue.seeking_description = form.seeking_talent_description.data

                db.session.add(venue)

                db.session.commit()

                db.session.close()
            except:
                flash('An error occurred. Venue '+ form.name.data + ' could not be listed.')
                db.session.rollback()
                db.session.close()
                return redirect(url_for('create_venue_submission'))

        return redirect(url_for("show_venue", venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------


@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)


@app.route("/artists/create", methods=["POST"])
def create_artist_submission():
    with db.session.no_autoflush:

        form = ArtistForm(request.form)

        if request.method == "POST" and form.validate():
            try:
                artist = Artist.get_or_create(db.session, name=form.name.data)

                artist.city = City.get_or_create(db.session, name=form.city.data, state=State.get_or_create(db.session, name=form.states.data))

                artist.phone = form.phone.data

                artist.genres = [Genre.get_or_create(db.session, name=g) for g in form.genres.data]
                artist.facebook_link = form.facebook_link.data
                artist.image_link = form.image_link.data
                artist.seeking_venue = form.seeking_venue.data
                artist.seeking_description = form.seeking_description.data
                artist.website = form.website_link
                db.session.add(artist)

                db.session.commit()

                db.session.close()
            except:
                flash('An error occurred. Artist '+ form.name.data + ' could not be listed.')
                db.session.rollback()
                db.session.close()
                return redirect(url_for('create_artist_submission'))

        return redirect(url_for('artists'))


#  Shows
#  ----------------------------------------------------------------


@app.route("/shows")
def shows():

    return render_template("pages/shows.html", shows=Show.query.all())


@app.route("/shows/create")
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template("forms/new_show.html", form=form)

@csrf.exempt
@app.route("/shows/search", methods=["POST"])
def search_shows():

    try:
        result = Show.query.filter(or_(Show.Artist.name.ilike(f"%{request.form.get('search_term').strip().lower()}%"),
                                       Show.Venue.name.ilike(f"%{request.form.get('search_term').strip().lower()}%"))
                                   ).all()
        count = len(result)
    except:
        result = None
        count =0

    response = {
        "count": count,
        "data": result,
    }

    return render_template(
        "pages/show.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )



@app.route("/shows/create", methods=["POST"])
def create_show_submission():
    with db.session.no_autoflush:

        form = ShowForm(request.form)

        if request.method == "POST" and form.validate():
            try:
                artist = Artist.query.filter_by(id=form.artist_id.data).one()
                venue = Venue.query.filter_by(id=form.venue_id.data).one()

                show = Show(Artist=artist, Venue=venue, start_time=form.start_time.data)

                db.session.add(show)

                db.session.commit()

                db.session.close()
            except Exception as e:
                print(e)
                flash('An error occurred. Show could not be added.')
                db.session.rollback()
                db.session.close()
                return redirect(url_for('create_shows'))

        return redirect(url_for('shows'))


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500


if not app.debug:
    file_handler = FileHandler("error.log")
    file_handler.setFormatter(
        Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info("errors")

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == "__main__":
    app.run()

# Or specify port manually:
"""
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
"""
