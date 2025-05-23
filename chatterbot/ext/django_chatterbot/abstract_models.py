from chatterbot.conversation import StatementMixin
from chatterbot import constants
from django.db import models
from django.utils import timezone
from django.conf import settings


DJANGO_APP_NAME = constants.DEFAULT_DJANGO_APP_NAME
STATEMENT_MODEL = 'Statement'
TAG_MODEL = 'Tag'

if hasattr(settings, 'CHATTERBOT'):
    """
    Allow related models to be overridden in the project settings.
    Default to the original settings if one is not defined.
    """
    DJANGO_APP_NAME = settings.CHATTERBOT.get(
        'django_app_name',
        DJANGO_APP_NAME
    )
    STATEMENT_MODEL = settings.CHATTERBOT.get(
        'statement_model',
        STATEMENT_MODEL
    )


class AbstractBaseTag(models.Model):
    """
    The abstract base tag allows other models to be created
    using the attributes that exist on the default models.
    """

    name = models.SlugField(
        max_length=constants.TAG_NAME_MAX_LENGTH,
        unique=True,
        help_text='The unique name of the tag.'
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class AbstractBaseStatement(models.Model, StatementMixin):
    """
    The abstract base statement allows other models to be created
    using the attributes that exist on the default models.
    """

    text = models.CharField(
        max_length=constants.STATEMENT_TEXT_MAX_LENGTH,
        help_text='The text of the statement.'
    )

    search_text = models.CharField(
        max_length=constants.STATEMENT_TEXT_MAX_LENGTH,
        blank=True,
        help_text='A modified version of the statement text optimized for searching.'
    )

    conversation = models.CharField(
        max_length=constants.CONVERSATION_LABEL_MAX_LENGTH,
        help_text='A label used to link this statement to a conversation.'
    )

    created_at = models.DateTimeField(
        default=timezone.now,
        help_text='The date and time that the statement was created at.'
    )

    in_response_to = models.CharField(
        max_length=constants.STATEMENT_TEXT_MAX_LENGTH,
        null=True,
        help_text='The text of the statement that this statement is in response to.'
    )

    search_in_response_to = models.CharField(
        max_length=constants.STATEMENT_TEXT_MAX_LENGTH,
        blank=True,
        help_text='A modified version of the in_response_to text optimized for searching.'
    )

    persona = models.CharField(
        max_length=constants.PERSONA_MAX_LENGTH,
        help_text='A label used to link this statement to a persona.'
    )

    tags = models.ManyToManyField(
        TAG_MODEL,
        related_name='statements',
        help_text='The tags that are associated with this statement.'
    )

    # This is the confidence with which the chat bot believes
    # this is an accurate response. This value is set when the
    # statement is returned by the chat bot.
    confidence = 0

    class Meta:
        abstract = True
        indexes = [
            models.Index(
                fields=['search_text'],
                name='idx_cb_search_text'
            ),
            models.Index(
                fields=['search_in_response_to'], name='idx_cb_search_in_response_to'
            ),
        ]

    def __str__(self):
        if len(self.text.strip()) > 60:
            return '{}...'.format(self.text[:57])
        elif len(self.text.strip()) > 0:
            return self.text
        return '<empty>'

    def get_tags(self) -> list[str]:
        """
        Return the list of tags for this statement.
        (Overrides the method from StatementMixin)
        """
        return list(self.tags.values_list('name', flat=True))

    def add_tags(self, *tags):
        """
        Add a list of strings to the statement as tags.
        (Overrides the method from StatementMixin)
        """
        for _tag in tags:
            self.tags.get_or_create(name=_tag)
