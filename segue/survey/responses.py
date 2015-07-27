from segue.responses import BaseResponse

class SurveyQuestionResponse(BaseResponse):
    def __init__(self, question):
        self.order    = question.order
        self.label    = question.label
        self.options  = question.options
        self.question = question.description
