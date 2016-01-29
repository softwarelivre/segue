from segue.responses import BaseResponse
from datetime import date

#FIX EMPTY NULL VALUES
#FIX DATE FORMAT

class AccountResponse(BaseResponse):
    def __init__(self, account):
        self.id = account.id
        self.name              = account.name
        self.city              = account.city
        self.role              = account.role
        self.phone             = account.phone
        self.email             = account.email
        self.country           = account.country
        self.created           = account.created
        self.document          = account.document
        self.badge_name        = account.badge_name or ''
        self.last_updated      = account.last_updated
        self.certificate_name  = account.certificate_name
        self.address_state     = account.address_state
        self.address_neighborhood = account.address_neighborhood
        self.address_street   = account.address_street
        self.address_number   = account.address_number
        self.address_extra    = account.address_extra or ''
        self.address_zipcode  = account.address_zipcode
        self.student_document = account.student_document or ''
        self.type = account.type
        self.dirty = account.dirty

        if account.type == 'person':
            if account.born_date:
                self.born_date = account.born_date.strftime("%d/%m/%Y")
            self.disability       = account.disability
            self.disability_info  = account.disability_info or ''
            self.sex              = account.sex
            self.occupation       = account.occupation
            self.education        = account.education
            self.membership       = account.membership
            self.resume            = account.resume or ''
            self.organization      = account.organization or ''
            self.has_filled_survey = account.survey_answers.count() > 0

        #REMOVE EMPTY VARIABLES
        for v in self.__dict__.keys():
            attr = getattr(self, v)
            if isinstance(attr, basestring) and not attr:
                delattr(self, v)

        self.address_extra    = account.address_extra or ''