from flask import Blueprint, send_file

from app.services.interfaces.iimage_service import ImageService
from app.utils.singleton import Singleton


class ImageController(Singleton):
    blueprint = Blueprint('image', __name__)
    service: ImageService = None

    @staticmethod
    @blueprint.route('/avatar/<username>', methods=['GET'])
    def getAvatar(username: str = 'default'):
        if username == 'default':
            return send_file(ImageController.service.get_default(), mimetype='image/png')
        """Serve the generated avatar image."""
        img_io = ImageController.service.get_avatar(username)
        return send_file(img_io, mimetype='image/png')
