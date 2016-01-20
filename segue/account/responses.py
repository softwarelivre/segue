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
        self.resume            = account.resume or ''
        self.country           = account.country
        self.created           = account.created
        self.document          = account.document
        self.badge_name        = account.badge_name or ''
        self.last_updated      = account.last_updated
        self.organization      = account.organization or ''
        self.certificate_name  = account.certificate_name
        self.disability       = account.disability
        self.disability_info  = account.disability_info or ''
        self.sex              = account.sex
        self.occupation       = account.occupation
        self.education        = account.education
        self.born_date        = account.born_date.strftime("%d/%m/%Y")
        self.address_state     = account.address_state
        self.address_neighborhood = account.address_neighborhood
        self.address_street   = account.address_street
        self.address_number   = account.address_number
        self.address_extra    = account.address_extra or ''
        self.address_zipcode  = account.address_zipcode
        self.membership = account.membership
        self.student_document = account.membership


        self.has_filled_survey = account.survey_answers.count() > 0
