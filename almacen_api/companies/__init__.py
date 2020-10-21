from .tag import tags_blueprint
from .entities import entities_blueprint, Entity
from .query import query_blueprint
from .feeds import feeds_blueprint
from .tags import url_tags_blueprint

companies_blueprints = [tags_blueprint, entities_blueprint, query_blueprint, feeds_blueprint, url_tags_blueprint]