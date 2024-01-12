from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contentctl.objects.deployment import Deployment        
    from contentctl.objects.security_content_object import SecurityContentObject
    from contentctl.objects.config import Config
    from contentctl.input.director import DirectorOutputDto
    
from contentctl.objects.enums import AnalyticsType
import re
import abc
import uuid
import datetime
from pydantic import BaseModel, field_validator, Field, ValidationInfo, FilePath, HttpUrl, NonNegativeInt, ConfigDict, model_validator
from typing import Tuple, Optional, List, Union
import pathlib
       




NO_FILE_NAME = "NO_FILE_NAME"
class SecurityContentObject_Abstract(BaseModel, abc.ABC):
    model_config = ConfigDict(use_enum_values=True,validate_default=True)
    # name: str = ...
    # author: str = Field(...,max_length=255)
    # date: datetime.date = Field(...)
    # version: NonNegativeInt = ...
    # id: uuid.UUID = Field(default_factory=uuid.uuid4) #we set a default here until all content has a uuid
    # description: str = Field(...,max_length=1000)
    # file_path: FilePath = Field(...)
    # references: Optional[List[HttpUrl]] = None
    
    name: str = Field("NO_NAME")
    author: str = Field("Content Author",max_length=255)
    date: datetime.date = Field(datetime.date.today())
    version: NonNegativeInt = 1
    id: uuid.UUID = Field(default_factory=uuid.uuid4) #we set a default here until all content has a uuid
    description: str = Field("Enter Description Here",max_length=10000)
    file_path: Optional[FilePath] = None
    references: Optional[List[HttpUrl]] = None


    @staticmethod
    def objectListToNameList(objects:list[SecurityContentObject], config:Optional[Config]=None)->list[str]:
        return [object.getName(config) for object in objects]

    # This function is overloadable by specific types if they want to redefine names, for example
    # to have the format ESCU - NAME - Rule (config.tag - self.name - Rule)
    def getName(self, config:Optional[Config])->str:
        return self.name

    @model_validator(mode="after")
    def ensureFileNameMatchesSearchName(self):
        file_name = self.name \
            .replace(' ', '_') \
            .replace('-','_') \
            .replace('.','_') \
            .replace('/','_') \
            .lower() + ".yml"
        
        if (self.file_path is not None and file_name != self.file_path.name):
            raise ValueError(f"The file name MUST be based off the content 'name' field:\n"\
                            f"\t- Expected File Name: {file_name}\n"\
                            f"\t- Actual File Name  : {self.file_path.name}")

        return self

    @field_validator('file_path')
    @classmethod
    def file_path_valid(cls, v: Optional[pathlib.PosixPath], info: ValidationInfo):
        if not v:
            #It's possible that the object has no file path - for example filter macros that are created at runtime
            return v
        if not v.name.endswith(".yml"):
            raise ValueError(f"All Security Content Objects must be YML files and end in .yml.  The following file does not: '{v}'")
        return v

    @field_validator('name','author','description')
    @classmethod
    def free_text_field_valid(cls, v: str, info:ValidationInfo)->str:
        try:
            v.encode('ascii')
        except UnicodeEncodeError as e:
            print(f"Potential Ascii encoding error in {info.field_name}:'{v}' - {str(e)}")
        except Exception as e:
            print(f"Unknown encoding error in {info.field_name}:'{v}' - {str(e)}")
        
        
        if bool(re.search(r"[^\\]\n", v)):
                raise ValueError(f"Unexpected newline(s) in {info.field_name}:'{v}'.  Newline characters MUST be prefixed with \\")
        return v
    
    @classmethod
    def mapNamesToSecurityContentObjects(cls, v: list[str], director:Union[DirectorOutputDto,None], allowed_type:type)->list[SecurityContentObject]:
        if director is not None:
            name_map = director.name_to_content_map
        else:
            name_map = {}
        


        mappedObjects: list[SecurityContentObject] = []
        missing_objects: list[str] = []
        for object_name in v:
            found_object = name_map.get(object_name,None)
            if not found_object:
                missing_objects.append(object_name)
            else:
                mappedObjects.append(found_object)
        
        if len(missing_objects) > 0:
            raise ValueError(f"Failed to find the following {allowed_type}: {missing_objects}")
        
        mistyped_objects = [f"{obj.name}: ACTUAL TYPE: '{type(obj)}'" for obj in mappedObjects if type(obj) != allowed_type]
        if len(mistyped_objects) > 0:
            bad_types_string = '\n - '.join([f"Bad object for {obj.name}: Expected type '{allowed_type}' but got type '{type(obj)}'" for obj in mistyped_objects])
            raise ValueError(f"Expected objects of type {allowed_type}, but got {len(mistyped_objects)} objects with unexpected types:\n - {bad_types_string}")


        return mappedObjects

    @staticmethod
    def getDeploymentFromType(typeField:Union[str,None], info:ValidationInfo)->Deployment:
        if typeField is None:
            raise ValueError("'type:' field is missing from YML.")
        director: Optional[DirectorOutputDto] = info.context.get("output_dto",None)
        if not director:
            raise ValueError("Cannot set deployment - DirectorOutputDto not passed to Detection Constructor in context")
        
        type_to_deployment_name_map = {AnalyticsType.TTP.value:"ESCU Default Configuration TTP", 
                                       AnalyticsType.Hunting.value:"ESCU Default Configuration Hunting", 
                                       AnalyticsType.Correlation.value: "ESCU Default Configuration Correlation", 
                                       AnalyticsType.Anomaly.value: "ESCU Default Configuration Anomaly", 
                                       "Baseline": "ESCU Default Configuration Baseline", 
        }
        converted_type_field = type_to_deployment_name_map[typeField]
        
        #TODO: This is clunky, but is imported here to resolve some circular import errors
        from contentctl.objects.deployment import Deployment 

        deployments = SecurityContentObject_Abstract.mapNamesToSecurityContentObjects([converted_type_field], director, Deployment)
        if len(deployments) == 1:
            return deployments[0]
        elif len(deployments) == 0:
            raise ValueError(f"Failed to find Deployment for type '{converted_type_field}' "\
                             f"from  possible {[deployment.type for deployment in director.deployments]}")
        else:
            raise ValueError(f"Found more than 1 ({len(deployments)}) Deployment for type '{converted_type_field}' "\
                             f"from  possible {[deployment.type for deployment in director.deployments]}")






    @staticmethod
    def get_objects_by_name(names_to_find:set[str], objects_to_search:list[SecurityContentObject_Abstract])->Tuple[list[SecurityContentObject_Abstract], set[str]]:
        raise Exception("get_objects_by_name deprecated")
        found_objects = list(filter(lambda obj: obj.name in names_to_find, objects_to_search))
        found_names = set([obj.name for obj in found_objects])
        missing_names = names_to_find - found_names
        return found_objects,missing_names
    
    @staticmethod
    def create_filename_to_content_dict(all_objects:list[SecurityContentObject_Abstract])->dict[str,SecurityContentObject_Abstract]:
        name_dict:dict[str,SecurityContentObject_Abstract] = dict()
        for object in all_objects:
            name_dict[str(pathlib.Path(object.file_path))] = object
        return name_dict
    

    
    