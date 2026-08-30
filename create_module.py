#!/usr/bin/env python3

import os
import re
import sys


def to_class_name(module_name: str) -> str:
    """
    Convert module name to PascalCase.

    Example:
        products -> Products
        product_reviews -> ProductReviews
    """
    parts = re.split(r"[_\-\s]+", module_name)
    return "".join(word.capitalize() for word in parts)


def validate_module_name(module_name: str):
    """
    Validate that the module name is a valid Python package name.
    """

    if not module_name:
        print("Error: Please provide a module name.")
        sys.exit(1)

    if not re.match(r"^[a-z][a-z0-9_]*$", module_name):
        print(
            "Error: Module name must start with a lowercase letter "
            "and contain only lowercase letters, numbers, and underscores."
        )
        sys.exit(1)


def get_file_templates(module_name: str) -> dict:
    """
    Return all file templates for the module.
    """

    class_name = to_class_name(module_name)

    return {

        "__init__.py": f'''"""
{class_name} module.
"""
''',

        "schemas.py": f'''"""
Schemas for the {module_name} module.

Pydantic schemas define the request and response data shapes.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict


class {class_name}Base(BaseModel):
    """
    Base schema containing common fields.
    """

    name: str
    description: Optional[str] = None


class {class_name}Create({class_name}Base):
    """
    Schema used when creating a new {module_name} resource.
    """

    pass


class {class_name}Update(BaseModel):
    """
    Schema used when updating a {module_name} resource.
    """

    name: Optional[str] = None
    description: Optional[str] = None


class {class_name}Response({class_name}Base):
    """
    Schema returned by the API.
    """

    id: int

    model_config = ConfigDict(from_attributes=True)
''',

        "repository.py": f'''"""
Repository layer for the {module_name} module.

This layer is responsible for database operations.
"""

from typing import Optional

from sqlmodel import Session


class {class_name}Repository:
    """
    Repository responsible for {module_name} database operations.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_all(self):
        """
        Fetch all records.

        Replace this example with actual SQLModel queries.
        """

        return []

    def get_by_id(self, item_id: int):
        """
        Fetch a single record by ID.

        Replace this example with an actual database query.
        """

        return None

    def create(self, data):
        """
        Create a new record.

        Replace this example with actual database persistence logic.
        """

        return {{
            "id": 1,
            **data.model_dump(),
        }}

    def update(self, item_id: int, data):
        """
        Update an existing record.

        Replace this example with actual database persistence logic.
        """

        update_data = data.model_dump(exclude_unset=True)

        return {{
            "id": item_id,
            **update_data,
        }}

    def delete(self, item_id: int):
        """
        Delete a record.

        Replace this example with actual database deletion logic.
        """

        return True
''',

        "service.py": f'''"""
Service layer for the {module_name} module.

This layer contains business logic.
"""

from .repository import {class_name}Repository
from .schemas import (
    {class_name}Create,
    {class_name}Update,
)


class {class_name}Service:
    """
    Service responsible for {module_name} business logic.
    """

    def __init__(self, repository: {class_name}Repository):
        self.repository = repository

    def get_all(self):
        """
        Get all {module_name}.
        """

        return self.repository.get_all()

    def get_by_id(self, item_id: int):
        """
        Get a single resource by ID.
        """

        return self.repository.get_by_id(item_id)

    def create(self, data: {class_name}Create):
        """
        Create a new resource.
        """

        # Add business validation here if needed.

        return self.repository.create(data)

    def update(self, item_id: int, data: {class_name}Update):
        """
        Update an existing resource.
        """

        existing_item = self.repository.get_by_id(item_id)

        if not existing_item:
            return None

        return self.repository.update(item_id, data)

    def delete(self, item_id: int):
        """
        Delete a resource.
        """

        existing_item = self.repository.get_by_id(item_id)

        if not existing_item:
            return False

        return self.repository.delete(item_id)
''',

        "dependencies.py": f'''"""
Dependency injection for the {module_name} module.

This file creates and provides dependencies required by the module.
"""

from fastapi import Depends
from sqlmodel import Session

from .repository import {class_name}Repository
from .service import {class_name}Service


def get_session() -> Session:
    """
    Provide a database session.

    IMPORTANT:
    Replace this with your project's actual database session dependency.

    Example:
        from app.core.database import get_session
    """

    raise NotImplementedError(
        "Connect get_session() to your application's database configuration."
    )


def get_{module_name}_repository(
    session: Session = Depends(get_session),
) -> {class_name}Repository:
    """
    Provide the repository dependency.
    """

    return {class_name}Repository(session)


def get_{module_name}_service(
    repository: {class_name}Repository = Depends(
        get_{module_name}_repository
    ),
) -> {class_name}Service:
    """
    Provide the service dependency.
    """

    return {class_name}Service(repository)
''',

        "controller.py": f'''"""
Controller layer for the {module_name} module.

The controller orchestrates request flow between routes and services.
"""

from fastapi import HTTPException, status

from .schemas import (
    {class_name}Create,
    {class_name}Update,
)
from .service import {class_name}Service


class {class_name}Controller:
    """
    Controller responsible for {module_name} request handling.
    """

    def __init__(self, service: {class_name}Service):
        self.service = service

    def get_all(self):
        """
        Handle fetching all resources.
        """

        return self.service.get_all()

    def get_by_id(self, item_id: int):
        """
        Handle fetching a resource by ID.
        """

        item = self.service.get_by_id(item_id)

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="{class_name} not found",
            )

        return item

    def create(self, data: {class_name}Create):
        """
        Handle resource creation.
        """

        return self.service.create(data)

    def update(
        self,
        item_id: int,
        data: {class_name}Update,
    ):
        """
        Handle resource update.
        """

        item = self.service.update(item_id, data)

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="{class_name} not found",
            )

        return item

    def delete(self, item_id: int):
        """
        Handle resource deletion.
        """

        deleted = self.service.delete(item_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="{class_name} not found",
            )

        return {{
            "message": "{class_name} deleted successfully"
        }}
''',

        "routes.py": f'''"""
Routes for the {module_name} module.

This layer handles HTTP endpoints and request/response handling.
"""

from typing import List

from fastapi import APIRouter, Depends, status

from .controller import {class_name}Controller
from .dependencies import get_{module_name}_service
from .schemas import (
    {class_name}Create,
    {class_name}Response,
    {class_name}Update,
)
from .service import {class_name}Service


router = APIRouter(
    prefix="/{module_name}",
    tags=["{class_name}"],
)


def get_controller(
    service: {class_name}Service = Depends(
        get_{module_name}_service
    ),
) -> {class_name}Controller:
    """
    Provide the controller dependency.
    """

    return {class_name}Controller(service)


@router.get(
    "/",
    response_model=List[{class_name}Response],
)
def get_all(
    controller: {class_name}Controller = Depends(
        get_controller
    ),
):
    """
    Get all resources.
    """

    return controller.get_all()


@router.get(
    "/{{item_id}}",
    response_model={class_name}Response,
)
def get_by_id(
    item_id: int,
    controller: {class_name}Controller = Depends(
        get_controller
    ),
):
    """
    Get a resource by ID.
    """

    return controller.get_by_id(item_id)


@router.post(
    "/",
    response_model={class_name}Response,
    status_code=status.HTTP_201_CREATED,
)
def create(
    data: {class_name}Create,
    controller: {class_name}Controller = Depends(
        get_controller
    ),
):
    """
    Create a new resource.
    """

    return controller.create(data)


@router.put(
    "/{{item_id}}",
    response_model={class_name}Response,
)
def update(
    item_id: int,
    data: {class_name}Update,
    controller: {class_name}Controller = Depends(
        get_controller
    ),
):
    """
    Update a resource.
    """

    return controller.update(item_id, data)


@router.delete(
    "/{{item_id}}",
    status_code=status.HTTP_200_OK,
)
def delete(
    item_id: int,
    controller: {class_name}Controller = Depends(
        get_controller
    ),
):
    """
    Delete a resource.
    """

    return controller.delete(item_id)
'''
    }


def create_module(module_name: str, is_blank: bool = False):
    """
    Create a complete FastAPI module.
    """

    validate_module_name(module_name)

    target_dir = os.path.join(
        "app",
        "modules",
        module_name,
    )

    # Check if module already exists
    if os.path.exists(target_dir):
        print(
            f"Error: Module '{module_name}' already exists "
            f"at {target_dir}"
        )
        sys.exit(1)

    try:
        # Create directory
        os.makedirs(target_dir, exist_ok=True)

        print(f"📁 Created directory: {target_dir}")

        # Get templates
        templates = get_file_templates(module_name)

        # Create files
        for filename, content in templates.items():

            file_path = os.path.join(
                target_dir,
                filename,
            )

            with open(
                file_path,
                "w",
                encoding="utf-8",
            ) as file:
                if not is_blank:
                    file.write(content)

            print(f"  📄 Created file: {filename}")

        print(
            f"\n🎉 Successfully created module "
            f"'{module_name}'!"
        )

        print("\nGenerated architecture:")
        print("Route")
        print("  ↓")
        print("Controller")
        print("  ↓")
        print("Service")
        print("  ↓")
        print("Repository")
        print("  ↓")
        print("Database")

        print("\nNext step:")
        print("Register the router in your main FastAPI application:\n")

        print(
            f"from app.modules.{module_name}.routes "
            f"import router as {module_name}_router"
        )

        print(
            f"\napp.include_router({module_name}_router)"
        )

    except Exception as error:
        print(f"An error occurred: {error}")
        sys.exit(1)


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print(
            "Usage: python create_module.py <module_name>"
        )
        sys.exit(1)

    name = sys.argv[1].strip().lower()
    is_blank = len(sys.argv) > 2 and sys.argv[2] == "--blank"

    create_module(name, is_blank)