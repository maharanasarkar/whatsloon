"""Template management models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TemplateSpec(BaseModel):
    """Template creation specification.

    Attributes:
        name: Template name (lowercase, underscores).
        language: Locale such as ``"en_US"``.
        category: One of MARKETING, UTILITY, AUTHENTICATION.
        components: Template components (header/body/buttons).
        allow_category_change: Whether Meta may recategorize.
    """

    name: str = Field(min_length=1)
    language: str = Field(min_length=1)
    category: str = "UTILITY"
    components: list[dict[str, Any]] = Field(default_factory=list)
    allow_category_change: bool = False

    def payload(self) -> dict[str, Any]:
        """Render the Meta creation payload.

        Returns:
            Creation payload.
        """
        return {
            "name": self.name,
            "language": self.language,
            "category": self.category,
            "components": self.components,
            "allow_category_change": self.allow_category_change,
        }


class TemplateInfo(BaseModel):
    """Listed template summary.

    Attributes:
        id: Meta template identifier.
        name: Template name.
        status: Approval status.
        language: Locale.
        category: Template category.
    """

    model_config = {"extra": "allow"}

    id: str = ""
    name: str = ""
    status: str = ""
    language: str = ""
    category: str = ""
