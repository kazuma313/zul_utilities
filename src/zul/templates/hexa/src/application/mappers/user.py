""" 
# Data Transfer Object (DTO)
DTOs are simple objects used to transfer data between different layers of an application 
or between services. dataclasses provide a convenient way to create them.

# Mapper
A mapper is responsible for converting data between different representations,
such as between a database entity and a DTO, or between a DTO and a response object.

"""

from dataclasses import dataclass

@dataclass
class UserDTO:
    id: int
    username: str
    email: str
    # No methods for business logic, just data

class UserEntity:
    def __init__(self, id: int, username: str, email: str, password_hash: str):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash # Sensitive data

class UserMapper:
    @staticmethod
    def to_dto(entity: UserEntity) -> UserDTO:
        """Converts a UserEntity to a UserDTO, omitting sensitive data."""
        return UserDTO(
            id=entity.id,
            username=entity.username,
            email=entity.email
        )

    @staticmethod
    def from_dto(dto: UserDTO, password_hash: str) -> UserEntity:
        """Converts a UserDTO back to a UserEntity (requires additional data)."""
        return UserEntity(
            id=dto.id,
            username=dto.username,
            email=dto.email,
            password_hash=password_hash
        )

# Example Usage
if __name__ == "__main__":
    # Simulate a UserEntity from a database
    db_user = UserEntity(id=1, username="john_doe", email="john@example.com", password_hash="hashed_password123")

    # Map entity to DTO for transfer or API response
    user_dto = UserMapper.to_dto(db_user)
    print(f"User DTO: {user_dto}")

    # Simulate creating/updating a user from DTO (requires password hash for entity)
    new_user_dto = UserDTO(id=2, username="jane_smith", email="jane@example.com")
    new_user_entity = UserMapper.from_dto(new_user_dto, "another_hashed_password")
    print(f"New User Entity: {new_user_entity.username}, {new_user_entity.email}, {new_user_entity.password_hash}")