from utils.defaults import (
    DEFAULT_DOMAIN,
    DEFAULT_LIMIT_SERP,
    DEFAULT_PAGES,
    DEFAULT_START_PAGE,
    DEFAULT_USER_AGENT,
    set_default_domain,
    set_default_limit,
    set_default_pages,
    set_default_start_page,
    set_default_user_agent,
    set_default_hotel_occupancy,
)
from utils.utils import (
    validate_url,
    Config,
    BaseGoogleOpts,
)
from utils.constants import Render, Domain, Source, Locale
import dataclasses
import utils.utils as utils


@dataclasses.dataclass
class GoogleSearchOpts(BaseGoogleOpts):
    domain: Domain = DEFAULT_DOMAIN
    start_page: int = DEFAULT_START_PAGE
    pages: int = DEFAULT_PAGES
    limit: int = DEFAULT_LIMIT_SERP
    locale: Locale = None

    AcceptedTbmParameters = [
        "app",
        "bks",
        "isch",
        "nws",
        "pts",
        "vid",
    ]

    def check_parameter_validity(self):
        utils.check_user_agent_validity(self.user_agent_type)
        utils.check_render_validity(self.render)
        utils.check_limit_validity(self.limit)
        utils.check_pages_validity(self.pages)
        utils.check_start_page_validity(self.start_page)

        # check if tbm parameter is valid
        if self.context:
            for opt in self.context:
                if (
                    opt.get("key") == "tbm"
                    and opt.get("value") not in self.AcceptedTbmParameters
                ):
                    raise ValueError(
                        f"Invalid tbm parameter value: {opt.get('value')}. Accepted values are: {', '.join(self.AcceptedTbmParameters)}"
                    )


@dataclasses.dataclass
class GoogleUrlOpts(BaseGoogleOpts):

    def check_parameter_validity(self):
        utils.check_user_agent_validity(self.user_agent_type)
        utils.check_render_validity(self.render)


@dataclasses.dataclass
class GoogleAdsOpts(BaseGoogleOpts):
    domain: Domain = None
    start_page: int = None
    pages: int = None
    locale: str = None

    AcceptedTbmParameters = [
        "app",
        "bks",
        "isch",
        "nws",
        "pts",
        "vid",
    ]

    def check_parameter_validity(self):
        utils.check_user_agent_validity(self.user_agent_type)
        utils.check_render_validity(self.render)
        utils.check_start_page_validity(self.start_page)

        if self.context:
            for opt in self.context:
                if (
                    opt.get("key") == "tbm"
                    and opt.get("value") not in self.AcceptedTbmParameters
                ):
                    raise ValueError(
                        f"Invalid tbm parameter value: {opt.get('value')}. Accepted values are: {', '.join(self.AcceptedTbmParameters)}"
                    )


@dataclasses.dataclass
class GoogleSuggestionsOpts(BaseGoogleOpts):
    locale: str = None

    def check_parameter_validity(self):
        utils.check_user_agent_validity(self.user_agent_type)
        utils.check_render_validity(self.render)


@dataclasses.dataclass
class GoogleHotelsOpts(BaseGoogleOpts):
    domain: Domain = DEFAULT_DOMAIN
    start_page: int = DEFAULT_START_PAGE
    pages: int = DEFAULT_PAGES
    limit: int = DEFAULT_LIMIT_SERP
    locale: str = None

    def check_parameter_validity(self):
        utils.check_user_agent_validity(self.user_agent_type)
        utils.check_render_validity(self.render)
        utils.check_limit_validity(self.limit)
        utils.check_pages_validity(self.pages)
        utils.check_start_page_validity(self.start_page)


@dataclasses.dataclass
class GoogleTravelHotelsOpts(BaseGoogleOpts):
    domain: Domain = None
    start_page: int = None
    locale: str = None

    def check_parameter_validity(self):
        utils.check_user_agent_validity(self.user_agent_type)
        utils.check_render_validity(self.render)
        utils.check_start_page_validity(self.start_page)


@dataclasses.dataclass
class GoogleImagesOpts(BaseGoogleOpts):
    domain: Domain = None
    start_page: int = None
    pages: int = None
    locale: str = None

    def check_parameter_validity(self):
        utils.check_render_validity(self.render)
        utils.check_start_page_validity(self.start_page)


@dataclasses.dataclass
class GoogleTrendsExploreOpts(BaseGoogleOpts):

    def check_parameter_validity(self):
        utils.check_user_agent_validity(self.user_agent_type)


class Google:

    def __init__(self, client):
        """
        Initializes a new instance of the Google class.

        Args:
            client (Client): The client to use for making requests.
        """
        self.client = client

    def scrape_google_search(self, query, opts=None, timeout: int = None):
        config = Config()

        if timeout is not None:
            config.set_timeout(timeout)

        else:
            config.reset_timeout()

        opts = GoogleSearchOpts(**opts if opts is not None else {})

        if (
            opts.limit is not None
            or opts.start_page is not None
            or opts.pages is not None
        ) and any(opt.get("key") == "limit_per_page" for opt in opts.context):
            raise ValueError(
                "limit, start_page, and pages parameters cannot be used together with limit_per_page context parameter"
            )

        # Set defaults
        opts.domain = set_default_domain(opts.domain)
        opts.start_page = set_default_start_page(opts.start_page)
        opts.limit = set_default_limit(opts.limit, DEFAULT_LIMIT_SERP)
        opts.pages = set_default_pages(opts.pages)
        opts.user_agent_type = set_default_user_agent(opts.user_agent_type)

        opts.check_parameter_validity()

        # Prepare payload
        payload = {
            "source": Source.GoogleSearch.value,
            "domain": opts.domain,
            "query": query,
            "locale": opts.locale,
            "geo_location": opts.geo_location,
            "user_agent_type": opts.user_agent_type,
            "render": opts.render,
            "callback_url": opts.callback_url,
            "parse": opts.parse,
            "context": opts.context,
        }

        # If user sends limit_per_page context parameter, use it instead of limit, start_page, and pages parameters.
        if opts.context and any(
            opt.get("key") == "limit_per_page" for opt in opts.context
        ):
            payload["limit"] = None
            payload["start_page"] = None
            payload["pages"] = None
        else:
            payload["limit"] = opts.limit
            payload["start_page"] = opts.start_page
            payload["pages"] = opts.pages

        # Add parsing instructions to the payload if provided
        if opts.parse_instructions is not None:
            payload["parsing_instructions"] = opts.parse_instructions
            payload["parse"] = True

        resp = self.client.send_post_request_with_payload(payload)

        return resp

    def scrape_google_url(self, url, opts=None, timeout=None):
        config = Config()

        if timeout is not None:
            config.set_timeout(timeout)

        else:
            config.reset_timeout()

        validate_url(url, "google")

        opts = GoogleUrlOpts(**opts if opts is not None else {})

        opts.user_agent_type = set_default_user_agent(opts.user_agent_type)

        opts.check_parameter_validity()

        # Prepare payload
        payload = {
            "source": Source.GoogleUrl.value,
            "url": url,
            "user_agent_type": opts.user_agent_type,
            "render": opts.render,
            "callback_url": opts.callback_url,
            "geo_location": opts.geo_location,
            "parse": opts.parse,
        }

        if opts.parse_instructions is not None:
            payload["parsing_instructions"] = opts.parse_instructions
            payload["parse"] = True

        resp = self.client.send_post_request_with_payload(payload)

        return resp

    def scrape_google_ads(self, query, opts=None, timeout=None):
        config = Config()

        if timeout is not None:
            config.set_timeout(timeout)

        else:
            config.reset_timeout()

        opts = GoogleAdsOpts(**opts if opts is not None else {})

        opts.domain = set_default_domain(opts.domain)
        opts.start_page = set_default_start_page(opts.start_page)
        opts.pages = set_default_pages(opts.pages)
        opts.user_agent_type = set_default_user_agent(opts.user_agent_type)

        opts.check_parameter_validity()

        # Prepare payload
        payload = {
            "source": Source.GoogleAds.value,
            "domain": opts.domain,
            "query": query,
            "locale": opts.locale,
            "geo_location": opts.geo_location,
            "user_agent_type": opts.user_agent_type,
            "render": opts.render,
            "callback_url": opts.callback_url,
            "parse": opts.parse,
            "context": opts.context,

        }

        if opts.parse_instructions is not None:
            payload["parsing_instructions"] = opts.parse_instructions
            payload["parse"] = True

        resp = self.client.send_post_request_with_payload(payload)

        return resp

    def scrape_google_suggestions(self, query, opts=None, timeout=None):
        config = Config()

        if timeout is not None:
            config.set_timeout(timeout)

        else:
            config.reset_timeout()

        opts = GoogleSuggestionsOpts(**opts if opts is not None else {})

        opts.user_agent_type = set_default_user_agent(opts.user_agent_type)

        opts.check_parameter_validity()

        # Prepare payload
        payload = {
            "source": Source.GoogleSuggestions.value,
            "query": query,
            "locale": opts.locale,
            "geo_location": opts.geo_location,
            "user_agent_type": opts.user_agent_type,
            "render": opts.render,
            "callback_url": opts.callback_url,
            "parse": opts.parse,
        }

        if opts.parse_instructions is not None:
            payload["parsing_instructions"] = opts.parse_instructions
            payload["parse"] = True

        resp = self.client.send_post_request_with_payload(payload)

        return resp

    def scrape_google_hotels(self, query, opts=None, timeout=None):
        config = Config()

        if timeout is not None:
            config.set_timeout(timeout)

        else:
            config.reset_timeout()

        opts = GoogleHotelsOpts(**opts if opts is not None else {})

        opts.domain = set_default_domain(opts.domain)
        opts.start_page = set_default_start_page(opts.start_page)
        opts.limit = set_default_limit(opts.limit, DEFAULT_LIMIT_SERP)
        opts.pages = set_default_pages(opts.pages)
        opts.user_agent_type = set_default_user_agent(opts.user_agent_type)
        opts.context = set_default_hotel_occupancy(opts.context)

        opts.check_parameter_validity()

        # Prepare payload
        payload = {
            "source": Source.GoogleHotels.value,
            "domain": opts.domain,
            "query": query,
            "start_page": opts.start_page,
            "pages": opts.pages,
            "limit": opts.limit,
            "locale": opts.locale,
            "geo_location": opts.geo_location,
            "user_agent_type": opts.user_agent_type,
            "render": opts.render,
            "callback_url": opts.callback_url,
            "parse": opts.parse,
            "context": opts.context,
        }

        if opts.parse_instructions is not None:
            payload["parsing_instructions"] = opts.parse_instructions
            payload["parse"] = True

        resp = self.client.send_post_request_with_payload(payload)

        return resp

    def scrape_google_travel_hotels(self, query, opts=None, timeout=None):
        config = Config()

        if timeout is not None:
            config.set_timeout(timeout)

        else:
            config.reset_timeout()

        opts = GoogleTravelHotelsOpts(**opts if opts is not None else {})

        opts.domain = set_default_domain(opts.domain)
        opts.start_page = set_default_start_page(opts.start_page)
        if 'context' in opts and opts['context']:
            for item in opts['context']:
                if item['key'] == 'hotel_occupancy':
                    item['value'] = set_default_hotel_occupancy(item.get('value'))

        opts.check_parameter_validity()

        # Prepare payload
        payload = {
            "source": Source.GoogleTravelHotels.value,
            "domain": opts.domain,
            "query": query,
            "start_page": opts.start_page,
            "locale": opts.locale,
            "geo_location": opts.geo_location,
            "user_agent_type": opts.user_agent_type,
            "render": opts.render if opts.render else Render.HTML.value,
            "callback_url": opts.callback_url,
            "parse": opts.parse,
            "context": opts.context,
        }

        if opts.parse_instructions is not None:
            payload["parsing_instructions"] = opts.parse_instructions
            payload["parse"] = True

        resp = self.client.send_post_request_with_payload(payload)

        return resp

    def scrape_google_images(self, query, opts=None, timeout=None):

        config = Config()

        if timeout is not None:
            config.set_timeout(timeout)

        else:
            config.reset_timeout()

        opts = GoogleImagesOpts(**opts if opts is not None else {})

        opts.user_agent_type = set_default_user_agent(opts.user_agent_type)
        opts.domain = set_default_domain(opts.domain)
        opts.start_page = set_default_start_page(opts.start_page)
        opts.pages = set_default_pages(opts.pages)

        opts.check_parameter_validity()

        # To scrape Google Image search, you must include the context:tbm parameter with the value set to isch.
        if opts.context is None or not any(
            opt.get("key") == "tbm" and opt.get("value") == "isch"
            for opt in opts.context
        ):
            if opts.context is None:
                opts.context = []
            opts.context.append({"key": "tbm", "value": "isch"})

        # Prepare payload
        payload = {
            "source": Source.GoogleSearch.value,
            "domain": opts.domain,
            "query": query,
            "start_page": opts.start_page,
            "pages": opts.pages,
            "locale": opts.locale,
            "geo_location": opts.geo_location,
            "user_agent_type": opts.user_agent_type,
            "render": opts.render,
            "callback_url": opts.callback_url,
            "parse": opts.parse,
            "context": opts.context,
        }

        if opts.parse_instructions is not None:
            payload["parsing_instructions"] = opts.parse_instructions
            payload["parse"] = True

        resp = self.client.send_post_request_with_payload(payload)

        return resp

    def scrape_google_trends_explore(self, query, opts=None, timeout=None):
        config = Config()

        if timeout is not None:
            config.set_timeout(timeout)

        else:
            config.reset_timeout()

        opts = GoogleTrendsExploreOpts(**opts if opts is not None else {})

        opts.user_agent_type = set_default_user_agent(opts.user_agent_type)

        opts.check_parameter_validity()

        # Prepare payload
        payload = {
            "source": Source.GoogleImages.value,
            "query": query,
            "geo_location": opts.geo_location,
            "context": opts.context,
            "user_agent_type": opts.user_agent_type,
            "callback_url": opts.callback_url,
            "parse": opts.parse,
        }

        if opts.parse_instructions is not None:
            payload["parsing_instructions"] = opts.parse_instructions
            payload["parse"] = True

        resp = self.client.send_post_request_with_payload(payload)

        return resp
