import json
import os

from flask import request, redirect, url_for, session, make_response, jsonify
from flask import Blueprint, render_template
from datetime import datetime

from app import AUTHENTICATED_ROLE, patreon_service
from app.annotations.authenticatedAnnotation import Authenticated
from app.annotations.requiredParamsAnnotation import RequiredParams
from app.language import words
from app.services.interfaces.idatabase_service import DatabaseService
from app.utils.singleton import Singleton


class DatabaseController(Singleton):
    blueprint = Blueprint('database', __name__)
    service: DatabaseService = None

    @staticmethod
    @blueprint.route('/facts/create', methods=['POST'])
    @Authenticated(required_roles=[AUTHENTICATED_ROLE])
    @RequiredParams()
    def createFact(title: str, context: str, page: int, quote: str, source_id: str, authentication: dict = None):
        user_id = authentication.get('sub')

        if any(len(s) > 512 for s in [title, context, quote, source_id]):
            return {'error': 'Some field is too long!'}, 422

        user_facts_count = DatabaseController.service.count_documents('facts', {'user_id': user_id})
        if user_facts_count >= int(os.getenv('FACTS_MAX_COUNT_DEFAULT', 10)):
            patreon_access_token = request.cookies.get('patreon_access_token', None)
            if patreon_access_token:
                user_cents = patreon_service.get_user_cents()
                if user_cents >= int(os.getenv('FACTS_CENTS_SUBSCRIBER', 100)):
                    if user_facts_count >= int(os.getenv('FACTS_MAX_COUNT_SUBSCRIBER', 100)):
                        return redirect(url_for('web.pleaseSubscribe', text=words[request.cookies.get('lang', 'en')]['max_subscriber'].replace('*', os.getenv("FACTS_MAX_COUNT_DEFAULT", 100))))
                else:
                    return redirect(url_for('web.pleaseSubscribe', text=words[request.cookies.get('lang', 'en')]['not_subscriber'].replace('*',os.getenv("FACTS_MAX_COUNT_DEFAULT", 10))))
            else:
                return redirect(url_for('web.pleaseSubscribe', text=words[request.cookies.get('lang', 'en')]['not_subscriber'].replace('*', os.getenv("FACTS_MAX_COUNT_DEFAULT", 10))))

        fact = DatabaseController.service.create_fact(title=title,
                                                      context=context,
                                                      page=page,
                                                      quote=quote,
                                                      source_id=source_id,
                                                      user_id=user_id)
        return redirect(f'/facts?_id={fact.get("_id", "")}')

    @staticmethod
    @blueprint.route('/sources/create', methods=['POST'])
    @Authenticated(required_roles=[AUTHENTICATED_ROLE])
    @RequiredParams()
    def createSource(title: str, author: str, year: int, _type_id: str, link: str, authentication: dict = None):
        user_id = authentication.get('sub')

        if any(len(s) > 512 for s in [title, author, _type_id, link]):
            return {'error': 'Some field is too long!'}, 422

        if DatabaseController.service.count_documents('sources', {}) >= os.getenv('SOURCES_MAX_COUNT', 10000):
            return {'error': 'Too many sources on server!'}, 403

        source = DatabaseController.service.create_source(title=title,
                                                          author=author,
                                                          year=year,
                                                          _type_id=_type_id,
                                                          link=link)
        return redirect(f'/sources?_id={source.get("_id", "")}')

    @staticmethod
    @blueprint.route('/react', methods=['POST'])
    @Authenticated(required_roles=[AUTHENTICATED_ROLE])
    @RequiredParams()
    def react(authentication: dict = None):
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400

        _id = data.get('_id')
        _collection = data.get('_collection')
        _label = data.get('_label')
        if not _id or not _collection or not _label:
            return jsonify({"error": "Invalid JSON data"}), 400

        user_id = authentication.get('sub')

        return {"response": DatabaseController.service.react(_id, _collection, _label, user_id)}

    @staticmethod
    @blueprint.route('/facts/create', methods=['POST'])
    @Authenticated(required_roles=[AUTHENTICATED_ROLE])
    @RequiredParams()
    def getProfileFacts(company_name: str = 'default', isCreate: bool = False, authentication: dict = None):
        document = DatabaseController.service.get_document('companies', {
            'name': company_name
        }) or {}

        employee = authentication.get('sub')
        if employee in document.get('employee', []):
            return render_template('company.html', company=document, authentication=authentication, isCreate=isCreate)
        return render_template('company.html', company={}, authentication=authentication, isCreate=isCreate)
