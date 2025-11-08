""" 
link references: https://hackernoon.com/dto-in-python-an-explanation

The primary goal of a DTO is to simplify communication between different layers of an application,
particularly when transmitting data through various boundary interfaces such as 
web services, REST APIs, message brokers, or other mechanisms of remote interaction.

example:
>>> user_dto = UserDTO(**{'first_name': 'John', 'lastName': 'Doe', 'age': 31})
>>> user_dto
UserDTO(first_name='John', last_name='Doe', age=31)

>>> user_dto.model_dump()
{'first_name': 'John', 'last_name': 'Doe', 'age': 31}

>>> user_dto.model_dump_json()
'{"first_name":"John","last_name":"Doe","age":31}'


>>> user_dto = UserDTO(**{'first_name': 'John', 'lastName': 'D', 'age': 3})
pydantic_core._pydantic_core.ValidationError: 2 validation errors for UserDTO
lastName
    String should have at least 2 characters [type=string_too_short, input_value='D', input_type=str]
age
    Value error, Age must be at least 18 [type=value_error, input_value=3, input_type=int]
"""

from pydantic import BaseModel, Field, field_validator

class UserDTO(BaseModel):
   first_name: str
   last_name: str = Field(min_length=2, alias="lastName")
   age: int = Field(lt=100, description="Age must be a positive integer")
   
   @field_validator("age")
   def validate_age(cls, value):
       if value < 18:
           raise ValueError("Age must be at least 18")
       return value