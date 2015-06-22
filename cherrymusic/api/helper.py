from rest_framework.renderers import BaseRenderer
from rest_framework.response import Response


class ImageResponse(Response):
    def __init__(self, image_data):
        #TODO: detect image type by file header
        super().__init__(
            content_type='image/jpg',
            headers={'Content-Length': len(image_data)},
            data=image_data
        )

class ImageRenderer(BaseRenderer):
    media_type = 'image/jpg'
    format = 'binary'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data