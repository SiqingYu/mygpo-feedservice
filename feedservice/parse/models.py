# -*- coding: utf-8 -*-
#

import re

from feedservice.utils import flatten, longest_substr
from feedservice.parse import mimetype


class ParserException(Exception):
    pass


class ParsedObject(object):

    _UNPROCESSED_FIELDS = ['link', 'urls', 'new_location', 'logo', 'hubs',
        'http_etag', 'flattr', 'license']

    def __init__(self, text_processor=None):
        super(ParsedObject, self).__init__()
        self._text_processor = text_processor


    def __setattr__(self, name, value):
        if isinstance(value, basestring):
            if getattr(self, '_text_processor', None):
                if not name in self._UNPROCESSED_FIELDS:
                    value = self._text_processor.process(value)

        object.__setattr__(self, name, value)


class Feed(ParsedObject):
    """ A parsed Feed """

    def __init__(self, text_processor=None):
        super(Feed, self).__init__(text_processor)
        self.errors = {}
        self.warnings = {}


    def add_error(self, key, msg):
        """ Adds an error entry to the feed """
        self.errors[key] = msg


    def add_warning(self, key, msg):
        """ Adds a warning entry to the feed """
        self.warnings[key] = msg


    def set_episodes(self, episodes):
        self.episodes = episodes

        self.content_types = self.get_content_types()
        self.common_title = self.get_common_title()

        for episode in self.episodes:
            episode._common_title = self.common_title



    def get_common_title(self):
        # We take all non-empty titles
        titles = filter(None, (e.title for e in self.episodes))

        # get the longest common substring
        common_title = longest_substr(titles)

        # but consider only the part up to the first number. Otherwise we risk
        # removing part of the number (eg if a feed contains episodes 100 - 199)
        common_title = re.search(r'^\D*', common_title).group(0)

        if len(common_title.strip()) < 2:
            return None

        return common_title



    def get_content_types(self):
        files = flatten(episode.files for episode in self.episodes)
        types = filter(None, (f.mimetype for f in files))
        return mimetype.get_podcast_types(types)



class Episode(ParsedObject):
    """ A parsed Episode """


    def __init__(self, text_processor=None):
        super(Episode, self).__init__(text_processor)


    @property
    def number(self):
        """
        Returns the first number in the non-repeating part of the episode's title
        """

        if None in (self.title, self._common_title):
            return None

        title = self.title.replace(self._common_title, '').strip()
        match = re.search(r'^\W*(\d+)', title)
        if not match:
            return None

        return int(match.group(1))


    def set_files(self, files):
        self.files = files
        self.content_types = self.get_content_types()


    @property
    def short_title(self):
        """
        Returns the non-repeating part of the episode's title
        If an episode number is found, it is removed
        """

        if None in (self.title, self._common_title):
            return None

        title = self.title.replace(self._common_title, '').strip()
        title = re.sub(r'^[\W\d]+', '', title)
        return title


    def get_content_types(self):
        types = filter(None, (f.mimetype for f in self.files))
        return mimetype.get_podcast_types(types)



class File(ParsedObject):


    def __init__(self, urls, mimetype=None, filesize=None):
        super(File, self).__init__(text_processor=None)

        self.urls = urls
        self.mimetype = mimetype
        self.filesize = filesize
