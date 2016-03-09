from segue.errors import SegueError, SegueGenericError
from segue.babel import _l

class DocumentNotFound(SegueError):
    code = 404
    def to_json(self):
        return { 'message': _l('could not find document {}'.format(self.args)) }


class InvalidDocument(SegueError):
    code = 404
    def to_json(self):
        return {'message': _l('Invalid document format.')}


class DocumentGenerationFailed(SegueError):
    code = 500
    def to_json(self):
        return {'message': _l('Document could not be generated.')}


class DocumentSaveFailed(SegueError):
    code = 500
    def to_json(self):
        return {'message': _l('Document could not be saved.')}
