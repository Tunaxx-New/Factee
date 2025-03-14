import os
from datetime import datetime

from bson import ObjectId
from flask import Blueprint, render_template, request

from app import AUTHENTICATED_ROLE
from app.annotations.authenticatedAnnotation import Authenticated
from app.controllers.authentication_controller import AuthenticationController
from app.controllers.database_controller import DatabaseController
from app.language import words

web_bp = Blueprint('web', __name__)


@web_bp.route('/', methods=['GET'])
def home():
    return render_template('index.html')


@web_bp.route('/facts/create', methods=['GET'])
@Authenticated(required_roles=[AUTHENTICATED_ROLE])
def createFactView(authentication: dict = None):
    return render_template('create_fact.html',
                           authentication=authentication,
                           sources=DatabaseController.service.get_documents('sources', {}))


@web_bp.route('/sources/create', methods=['GET'])
@Authenticated(required_roles=[AUTHENTICATED_ROLE])
def createSourceView(authentication: dict = None):
    return render_template('create_source.html',
                           authentication=authentication,
                           types=DatabaseController.service.get_documents('types', {}))


def get_cards(collection: str, isSource=False):
    username = request.args.get('username', None)
    title = request.args.get('title', None)
    year = request.args.get('year', None)
    sort_field = request.args.get('sort', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    page = int(request.args.get('page', 1))  # Default to page 1
    limit = int(request.args.get('limit', 10))  # Default to 10 documents per page
    if limit > 100:
        limit = 100
    skip = (page - 1) * limit

    # Build match filter
    match_filter = {}
    if username:
        users = AuthenticationController.service.get_public_info_by_username(username)
        user_id = users[0].get('id', '') if users else '^$'
        if isSource:
            match_filter['user_id'] = {'$regex': user_id, '$options': 'i'}
        else:
            match_filter['author'] = {'$regex': username, '$options': 'i'}
    if title:
        match_filter['title'] = {'$regex': title, '$options': 'i'}
    if year:
        start_date = datetime(int(year), 1, 1)
        end_date = datetime(int(year) + 1, 1, 1)
        match_filter['created_at'] = {'$gte': start_date, '$lt': end_date}

    sort_label = DatabaseController.service.get_document('labels', {'name': sort_field}) or {'_id': '^$'}
    if sort_label:
        sort_field = "sortLabelUsersCount"

    pipeline = [
        {"$match": match_filter},  # Filter data
        {"$addFields": {"reactions_count": {"$size": {"$ifNull": ["$reactions", []]}}}},  # Count reactions
        {"$addFields": {
            "sortLabelUsersCount": {
                "$sum": {
                    "$map": {
                        "input": {
                            "$filter": {
                                "input": "$labels",
                                "as": "label",
                                "cond": {"$eq": ["$$label.label_id", sort_label.get('_id')]}
                            }
                        },
                        "as": "filtered_label",
                        "in": {"$size": "$$filtered_label.users"}
                    }
                }
            }
        }},
        {"$sort": {sort_field: sort_order}},  # Sort dynamically
        {"$skip": skip},  # Skip documents for pagination
        {"$limit": limit}
    ]

    cards = DatabaseController.service.get_documents_pipeline(collection, pipeline)
    total_cards = DatabaseController.service.count_documents(collection, match_filter)
    total_pages = (total_cards + limit - 1) // limit

    labels = DatabaseController.service.get_documents('labels', {})
    sorted_labels = sorted(labels, key=lambda x: x.get("order", 0))

    return cards, sorted_labels, page, limit, total_pages


@web_bp.route('/sources', methods=['GET'])
def sourcesView(_id: str = None):
    _id = request.args.get('_id')
    baked = request.args.get('baked', '')

    if _id:
        labels = DatabaseController.service.get_documents('labels', {})
        sorted_labels = sorted(labels, key=lambda x: x.get("order", 0))

        source = DatabaseController.service.get_document('sources', {'_id': ObjectId(_id)})
        return render_template('source.html',
                               source=source,
                               labels=sorted_labels)
    else:
        if baked:
            return render_template('baked.html',
                                   baked=baked,
                                   factOrSourceRoute='sources',
                                   factOrSource=words[request.cookies.get('lang', 'en')]['source'])
        sources, labels, page, limit, total_pages = get_cards('sources')

        for source in sources:
            source['user'] = {'username': source.get('author', '')}

            labels_ = []
            for label in labels:
                label_id = label.get('_id')
                matching_label = next((l for l in source.get('labels', []) if l.get('label_id', {}) == label_id), None)
                labels_.append({'id': label_id,
                                'icon': label.get('icon', label.get('name', '')),
                                'name': label.get('name'),
                                'color': label.get('color'),
                                'count': len(matching_label.get('users', [])) if matching_label else 0})
            source['labels_'] = labels_

        return render_template('cards.html',
                               title=words[request.cookies.get('lang', 'en')]['source_list'],
                               cards=sources,
                               page=page,
                               limit=limit,
                               labels=labels,
                               total_pages=total_pages,
                               redirect='web.sourcesView')


@web_bp.route('/facts', methods=['GET'])
@Authenticated(required_roles=[], is_necessary=False)
def factsView(authentication: dict = None):
    _id = request.args.get('_id', None)
    baked = request.args.get('baked', '')

    if _id:
        fact = DatabaseController.service.get_document('facts', {'_id': ObjectId(_id)})
        if fact:
            labels = DatabaseController.service.get_documents('labels', {})
            user = AuthenticationController.service.get_public_info(fact.get('user_id'))
            sorted_labels = sorted(labels, key=lambda x: x.get("order", 0))
            source = DatabaseController.service.get_document('sources', {'_id': ObjectId(fact.get('source_id'))})
            type = DatabaseController.service.get_document('types', {'_id': ObjectId(source.get('type'))})
            return render_template('fact.html',
                                   fact=fact,
                                   user=user,
                                   self_user_id=authentication.get('sub', None),
                                   source=source,
                                   type=type,
                                   labels=sorted_labels,
                                   _primary_color=type.get('color'))
        else:
            return render_template('baked.html',
                                   baked=baked,
                                   factOrSourceRoute='facts',
                                   factOrSource=words[request.cookies.get('lang', 'en')]['fact'])
    else:
        if baked:
            return render_template('baked.html',
                                   baked=baked,
                                   factOrSourceRoute='facts',
                                   factOrSource=words[request.cookies.get('lang', 'en')]['fact'])

        facts, labels, page, limit, total_pages = get_cards('facts')

        for fact in facts:
            fact['user'] = AuthenticationController.service.get_public_info(fact.get('user_id'))
            labels_ = []
            for label in labels:
                label_id = label.get('_id')
                matching_label = next((l for l in fact.get('labels', []) if l.get('label_id', {}) == label_id), None)
                labels_.append({'id': label_id,
                                'icon': label.get('icon', label.get('name', '')),
                                'name': label.get('name'),
                                'color': label.get('color'),
                                'count': len(matching_label.get('users', [])) if matching_label else 0})
            fact['labels_'] = labels_

        return render_template('cards.html',
                               title=words[request.cookies.get('lang', 'en')]['fact_list'],
                               cards=facts,
                               page=page,
                               limit=limit,
                               labels=labels,
                               total_pages=total_pages,
                               redirect='web.factsView')


@web_bp.route('/how', methods=['GET'])
def howTo():
    language = request.cookies.get('lang', 'en')
    return render_template(f'baked/how_{language}.html',
                           labels=sorted(DatabaseController.service.get_documents('labels', {}), key=lambda x: x['order']),
                           types=sorted(DatabaseController.service.get_documents('types', {}), key=lambda x: x['name']))


@web_bp.route('/redirect', methods=['GET'])
def onRedirect():
    redirect = request.args.get('redirect', request.referrer)
    return render_template(f'redirect.html', redirect=redirect)


@web_bp.route('/pleaseSubscribe', methods=['GET'])
def pleaseSubscribe():
    text = request.args.get('text', '')
    return render_template('please_subscribe.html',
                           text=text)
