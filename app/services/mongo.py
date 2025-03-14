from datetime import datetime
from typing import Tuple, Dict

from bson import ObjectId
from pymongo import MongoClient, ReturnDocument, DESCENDING, ASCENDING

from app.services.interfaces.idatabase_service import DatabaseService


class Mongo(DatabaseService):

    def react(self, _id: str, _collection: str, _label: str, user_id: str) -> tuple[dict[str, str], int]:
        collection = self.db[_collection]
        reactions_collection = self.db['labels']
        document = collection.find_one({"_id": ObjectId(_id)})

        label_exists = reactions_collection.find_one({"name": _label})
        if not label_exists:
            return {"error": f"Label '{_label}' does not exist in labels collection"}, 400

        if not document:
            return {"error": "Document not found"}, 400

        # Find the label inside the labels array
        labels = document.get('labels', [])
        for label in labels:
            if str(label["label_id"]) == str(label_exists.get('_id')):
                if user_id not in label["users"]:
                    # Append user to the label's user list
                    collection.update_one(
                        {"_id": ObjectId(_id), "labels.label_id": ObjectId(label_exists.get('_id'))},
                        {"$addToSet": {"labels.$.users": user_id}}
                    )
                    return {"message": f"User {user_id} reacted with {_label}"}, 200
                else:
                    collection.update_one(
                        {"_id": ObjectId(_id), "labels.label_id": ObjectId(label_exists.get('_id'))},
                        {"$pull": {"labels.$.users": user_id}}
                    )
                    return {"message": f"User {user_id} dereacted with {_label}"}, 200

        # If label does not exist in document, add it
        collection.update_one(
            {"_id": ObjectId(_id)},
            {"$push": {"labels": {"label_id": ObjectId(label_exists.get('_id')), "users": [user_id]}}}
        )

        return {"message": f"User {user_id} reacted with created {_label}"}, 200

    def create_fact(self, title: str, context: str, page: int, quote: str, source_id: str, user_id: str) -> dict:
        if source_id is None or source_id == "":
            return {"error": "Source is missing"}
        if user_id is None or user_id == "":
            return {"error": "User is missing"}

        collection = self.db['facts']
        query = {'title': title}
        document = {
            'title': title,
            'context': context,
            'page': page,
            'quote': quote,
            'source_id': ObjectId(source_id),
            'user_id': user_id,
            'labels': [],
            'created_at': datetime.utcnow(),
        }
        return dict(collection.find_one_and_update(query, {"$set": document}, upsert=True, return_document=ReturnDocument.AFTER))

    def create_source(self, title: str, author: str, year: int, _type_id: str, link: str) -> dict:
        type_exists = self.db['types'].find_one({"_id": ObjectId(_type_id)})
        if not type_exists:
            return {"error": f"Label '{_type_id}' does not exist in labels collection"}

        collection = self.db['sources']
        query = {'title': title}
        document = {
            'title': title,
            'author': author,
            'year': year,
            'type': ObjectId(_type_id),
            'link': link,
            'labels': [],
            'created_at': datetime.utcnow(),
        }
        return dict(collection.find_one_and_update(query, {"$set": document}, upsert=True,
                                                   return_document=ReturnDocument.AFTER))

    def __init__(self, database_name, host):
        self.client = MongoClient(host)
        self.db = self.client[database_name]

    def get_documents(self, collection: str, query: dict) -> list[dict]:
        collection = self.db[collection]
        return list(collection.find(query))

    def get_documents_pipeline(self, collection: str, pipeline: list) -> list[dict]:
        for stage in pipeline:
            if "$sort" in stage:
                sort_field = list(stage["$sort"].keys())[0]
                sort_order_str = list(stage["$sort"].values())[0]
                stage["$sort"][sort_field] = DESCENDING if sort_order_str.lower() == "desc" else ASCENDING
                break

        collection = self.db[collection]
        return list(collection.aggregate(pipeline))

    def get_document(self, collection: str, query: dict) -> dict:
        collection = self.db[collection]
        return collection.find_one(query)

    def count_documents(self, collection: str, query: dict) -> int:
        collection = self.db[collection]
        return collection.count_documents(query)

    def get_user_summary(self, user_id: str):
        pipeline = [
            {"$match": {"user_id": user_id}},  # Filter documents by user_id
            {"$unwind": "$labels"},  # Flatten the labels array
            {
                "$group": {
                    "_id": "$labels.label_id",  # Group by label_id
                    "reaction_count": {"$sum": {"$size": "$labels.users"}},  # Count users (reactions) per label
                }
            },
            {"$sort": {"reaction_count": -1}}  # Sort by most reactions
        ]
        label_summary = list(self.db['facts'].aggregate(pipeline))
        labels = self.get_documents('labels', {})
        for label in labels:
            label_source = None
            for l in label_summary:
                if l.get('_id') == label.get('_id'):
                    label_source = l
            label.update({'reaction_count': label_source.get('reaction_count') if label_source else 0})

        pipeline = [
            {"$match": {"user_id": {"$exists": True, "$eq": user_id}}},  # Filter where user_id matches
            {
                "$project": {
                    "_id": 1,  # Include document ID
                    "title": 1,  # Include title
                    "source_id": 1  # Include labels array
                }
            },
            {
                "$lookup": {
                    "from": "sources",        # Collection to join
                    "localField": "source_id", # Field in current collection
                    "foreignField": "_id",     # Field in 'sources' collection
                    "as": "source_info",        # Output field
                    "pipeline": [
                        {
                            "$lookup": {  # Second lookup for type details
                                "from": "types",
                                "localField": "type",
                                "foreignField": "_id",
                                "as": "type_info"
                            }
                        },
                        {
                            "$project": {  # Projection inside lookup
                                "_id": 1,  # Include _id
                                "title": 1,  # Include source name
                                "author": 1,  # Include publication year
                                "year": 1,  # Include publication year
                                "type_info": 1  # Include publication year
                            }
                        }
                    ]
                }
            },
        ]
        facts = list(self.db['facts'].aggregate(pipeline))

        return facts, labels

