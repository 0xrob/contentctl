import abc
import string
import uuid
from datetime import datetime
from pydantic import BaseModel, validator, ValidationError
from contentctl.objects.enums import SecurityContentType
import uuid

class SecurityContentObject_Abstract(BaseModel, abc.ABC):
    contentType: SecurityContentType
    name: str
    author: str = "UNKNOWN_AUTHOR"
    date: str = "1990-01-01"
    version: int = 1
    id: uuid.UUID = uuid.uuid4() #we set a default here until all content has a uuid
    description: str = "UNKNOWN_DESCRIPTION"

    @validator('name')
    def name_max_length(cls, v):
        if len(v) > 67:
            raise ValueError('name is longer then 67 chars: ' + v)
        return v

    @validator('name')
    def name_invalid_chars(cls, v):
        invalidChars = set(string.punctuation.replace("-", ""))
        if any(char in invalidChars for char in v):
            raise ValueError('invalid chars used in name: ' + v)
        return v

    @validator('date')
    def date_valid(cls, v, values):
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except:
            raise ValueError('date is not in format YYYY-MM-DD: ' + values["name"])
        return v

    @staticmethod
    def free_text_field_valid(input_cls, v, values, field):
        try:
            v.encode('ascii')
        except UnicodeEncodeError:
            raise ValueError('encoding error in ' + field.name + ': ' + values["name"])
        return v
    
    @validator('description')
    def description_valid(cls, v, values, field):
        return SecurityContentObject_Abstract.free_text_field_valid(cls,v,values,field)