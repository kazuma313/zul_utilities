"""
Contoh DTO (Data Transfer Object) dengan Pydantic.

Gunanya:
    DTO menyederhanakan pertukaran data antar layer dan lewat batas aplikasi
    seperti REST API atau message broker. DTO hanya membawa data yang sudah
    divalidasi; tidak ada logika bisnis di dalamnya.
    Rujukan: https://hackernoon.com/dto-in-python-an-explanation

Cara pakai:
    >>> user_dto = UserDTO(**{"first_name": "John", "lastName": "Doe", "age": 31})
    >>> user_dto
    UserDTO(first_name='John', last_name='Doe', age=31)

    >>> user_dto.model_dump()
    {'first_name': 'John', 'last_name': 'Doe', 'age': 31}

    >>> user_dto.model_dump_json()
    '{"first_name":"John","last_name":"Doe","age":31}'

Contoh data yang ditolak:
    >>> UserDTO(**{"first_name": "John", "lastName": "D", "age": 3})
    pydantic_core._pydantic_core.ValidationError: 2 validation errors for UserDTO
    lastName
        String should have at least 2 characters [type=string_too_short, ...]
    age
        Value error, Age must be at least 18 [type=value_error, ...]
"""

from pydantic import BaseModel, Field, field_validator


class UserDTO(BaseModel):
    first_name: str
    last_name: str = Field(min_length=2, alias="lastName")
    age: int = Field(lt=100, description="Age must be a positive integer")

    @field_validator("age")
    @classmethod
    def validate_age(cls, value: int) -> int:
        if value < 18:
            raise ValueError("Age must be at least 18")

        return value
