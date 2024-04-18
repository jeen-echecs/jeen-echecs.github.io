AUTHOR = 'msa'
SITENAME = 'Le club du JÉEN'
SITEURL = '.'

PATH = 'content'

# Theme
THEME = 'themes/pelican-bootstrap3'
#BOOTSTRAP_THEME = 'lux'

TIMEZONE = 'Europe/Paris'

DEFAULT_LANG = 'fr'
FAVICON = u'images/favicon.ico'

PLUGIN_PATHS = ['pelican-plugins']
PLUGINS = ['i18n_subsites', 'photos', 'seo', 'sitemap']
JINJA_ENVIRONMENT = {
    'extensions': ['jinja2.ext.i18n'],
}

STATIC_PATHS = ['images', 'static', 'extra/CNAME', 'extra/.nojekyll']
EXTRA_PATH_METADATA = { 'extra/CNAME': {'path': 'CNAME'},
                        'extra/.nojekyll': {'path': '.nojekyll'},
                      }

DEFAULT_PAGINATION = 5

SITEMAP = {
    "format": "xml",
}

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
LINKS = (
         ('Fiche FFE du club', 'http://www.echecs.asso.fr/FicheClub.aspx?Ref=836'),
         ('Equipes du club', 'http://www.echecs.asso.fr/ListeEquipes.aspx?ClubRef=836'),
         ('Paris Echecs', 'https://echecs.paris/index.php'),
         ('Ligue Ile de France', 'https://idf-echecs.com/pages/'),
         ('FFE', 'http://www.echecs.asso.fr/'),
	 ('Lichess', 'https://lichess.org/'),
        )

# Sidebar Images
SIDEBAR_IMAGES_HEADER = 'Partenaires'
SIDEBAR_IMAGES = (
    ('/static/ffe_logo.jpg'),
    ('/static/ans_logo_rvb_x2.jpg'),
    ('/static/ville_de_paris_logo.png'),
)

# Social widget
# SOCIAL = (('Twitter', 'https://twitter.com/JEEN_Echecs'),
#         )

# Uncomment following line if you want document-relative URLs when developing
RELATIVE_URLS = True

MARKDOWN = {
    'extension_configs': {
        'markdown.extensions.codehilite': {'css_class': 'highlight'},
        'markdown.extensions.extra': {},
        'markdown.extensions.meta': {},
    },
    'output_format': 'html5',
}

SUMMARY_MAX_LENGTH = 200

# Configuring the header and the menu
BOOTSTRAP_NAVBAR_INVERSE = False
SITELOGO = 'images/logo-highres.jpg'
SITELOGO_SIZE = "50px"
HIDE_SITENAME = True
BANNER = 'images/banner.jpg'
BANNER_ALL_PAGES = True

DISPLAY_CATEGORIES_ON_MENU = False
DISPLAY_PAGES_ON_MENU = False
MENUITEMS = (
    ('Présentation', '/pages/presentation-du-club.html'),
    ('Inscriptions', '/pages/inscriptions.html'),
    ('Histoire et Palmarès', '/pages/histoire-et-palmares.html'),
)


# Twitter timeline in sidebar
# TWITTER_USERNAME = "JEEN_Echecs"
# TWITTER_WIDGET_ID = 1234

# Configuration for photos
PHOTO_LIBRARY = "photos"
PHOTO_GALLERY = (1024, 768, 80)
PHOTO_ARTICLE = (760, 506, 80)
PHOTO_INLINE_GALLERY_ENABLED = True
PHOTO_RESIZE_JOBS = -1
PHOTO_DEFAULT_IMAGE_OPTIONS = {
	"jpeg": {
		"optimize": True
	}
}
