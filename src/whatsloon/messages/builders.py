"""Fluent builders for interactive message content.

Builders assemble rows and buttons incrementally while enforcing the same
limits as the models, so callers fail fast before serialization.
"""

from __future__ import annotations

from typing import Any, Optional

from whatsloon.messages.models import ListMessage, ReplyButton, ReplyButtonsMessage


class ListBuilder:
    """Incrementally build an interactive list message.

    Attributes:
        body_text: Body text.
        button_text: Button label.
    """

    def __init__(self, body_text: str, button_text: str) -> None:
        """Initialize the builder.

        Args:
            body_text: Body text.
            button_text: Button label.
        """
        self.body_text = body_text
        self.button_text = button_text
        self._sections: list[dict[str, Any]] = []
        self._header: Optional[dict[str, Any]] = None
        self._footer: Optional[str] = None

    def header(self, header: dict[str, Any]) -> ListBuilder:
        """Set the header object.

        Args:
            header: Header object.

        Returns:
            This builder.
        """
        self._header = header
        return self

    def footer(self, footer_text: str) -> ListBuilder:
        """Set the footer text.

        Args:
            footer_text: Footer text.

        Returns:
            This builder.
        """
        self._footer = footer_text
        return self

    def section(self, title: str, rows: list[dict[str, Any]]) -> ListBuilder:
        """Append a section.

        Args:
            title: Section title.
            rows: Section rows.

        Returns:
            This builder.
        """
        self._sections.append({"title": title, "rows": rows})
        return self

    def build(self) -> ListMessage:
        """Build the validated list message.

        Returns:
            Validated list message.

        Raises:
            ValueError: If 2.x section/row limits are exceeded.
        """
        return ListMessage(
            body_text=self.body_text,
            button_text=self.button_text,
            sections=self._sections,
            header=self._header,
            footer_text=self._footer,
        )


class ButtonsBuilder:
    """Incrementally build a reply-button message.

    Attributes:
        body_text: Body text.
    """

    def __init__(self, body_text: str) -> None:
        """Initialize the builder.

        Args:
            body_text: Body text.
        """
        self.body_text = body_text
        self._buttons: list[ReplyButton] = []
        self._header: Optional[dict[str, Any]] = None
        self._footer: Optional[str] = None

    def button(self, button_id: str, title: str) -> ButtonsBuilder:
        """Append a button.

        Args:
            button_id: Button identifier.
            title: Button title.

        Returns:
            This builder.
        """
        self._buttons.append(ReplyButton(id=button_id, title=title))
        return self

    def header(self, header: dict[str, Any]) -> ButtonsBuilder:
        """Set the header object.

        Args:
            header: Header object.

        Returns:
            This builder.
        """
        self._header = header
        return self

    def footer(self, footer_text: str) -> ButtonsBuilder:
        """Set the footer text.

        Args:
            footer_text: Footer text.

        Returns:
            This builder.
        """
        self._footer = footer_text
        return self

    def build(self) -> ReplyButtonsMessage:
        """Build the validated button message.

        Returns:
            Validated reply-button message.

        Raises:
            ValueError: If button count or title limits are exceeded.
        """
        return ReplyButtonsMessage(
            body_text=self.body_text,
            buttons=self._buttons,
            header=self._header,
            footer_text=self._footer,
        )


__all__ = ["ButtonsBuilder", "ListBuilder"]
