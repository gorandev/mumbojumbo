import scrapy
from dateutil.parser import parse
from govpredict.items import GovPredictItem


class FaraSpider(scrapy.Spider):
    name = "fara"

    def start_requests(self):
        # we start by getting the IFRAME with the links
        # TODO: we should get https://www.fara.gov/quick-search.html
        # and pick up the IFRAME URL from there. One thing at a time. :)
        return [scrapy.Request(
                "https://efile.fara.gov/pls/apex/f?p=171:1:0:::::",
                callback=self.get_active_foreign_principals,
                dont_filter=True)]
        # the dont_filter=True allows Scrapy to follow the 302
        # instead of filtering it as a dupe

    def get_active_foreign_principals(self, response):
        # we have the cookies and the menu,
        # we search for the link for active foreign principals
        fp_url = scrapy.Selector(
            response=response
        ).xpath(
            "//font[.='Active Foreign Principals']/../@href"
        ).extract_first()
        # TODO: need to catch null values of fp_url here
        return [scrapy.Request('https://efile.fara.gov/pls/apex/' + fp_url,
                callback=self.get_active_foreign_principals_datapage)]

    def get_active_foreign_principals_datapage(self, response):
        # this method will return items to parse and the next request
        # if page is None, then it's the first page
        # otherwise we'll make the request
        # with the appropiate values for the next page

        # the p_instance needs to be picked up from the first page, so it will
        # also be None on the first pass

        if \
            "the source data of the report has been modified." \
                in response.body:
            # this means we've ran out of pages
            yield None
            return

        # response could be sent to another method so we don't clutter this one
        #
        # basically on the first pass we send the response to another method
        # if page is none we'll use pgR_min_row=16 on the first run,
        # set page to 1
        # so pgR will be page * 15 + 1
        # and we also set the p_instance
        #
        # on later passes, we'll just send the response to the other method

        page = response.meta.get('page')
        p_instance = response.meta.get('p_instance')

        if page is None and p_instance is None:
            page = 1
            p_instance = scrapy.Selector(
                response=response
            ).xpath(
                "//input[@id='pInstance']/@value"
            ).extract_first()

        # TODO: we should pick up from the HTML as much as needed from this
        # hardcoding is never good and some fields might change now and then
        post_page_fields = {
            'p_request': 'APXWGT',
            'p_instance': p_instance,
            'p_flow_id': 171,
            'p_flow_step_id': 130,
            'p_widget_num_return': 15,
            'p_widget_name': 'worksheet',
            'p_widget_mod': 'ACTION',
            'p_widget_action': 'PAGE',
            'p_widget_action_mod':
                'pgR_min_row=%smax_rows=15rows_fetched=15' %
                ((page * 15) + 1,),
            'x01': 80340213897823017,
            'x02': 80341508791823021
        }
        post_page_fields_string = \
            '&'.join(
                "%s=%s" % (key, val) for (key, val) in post_page_fields.items()
            )

        request = scrapy.Request(
            'https://efile.fara.gov/pls/apex/wwv_flow.show',
            method='POST',
            body=post_page_fields_string,
            callback=self.get_active_foreign_principals_datapage
        )
        request.meta['page'] = page + 1
        request.meta['p_instance'] = p_instance
        yield request

        for tr in response.xpath(
            "//tr[@class='odd' or @class='even']"
        ).extract():
            selector = scrapy.Selector(text=tr)
            # TODO: an ItemLoader would be great here
            foreign_principal = GovPredictItem(
                url='https://efile.fara.gov/pls/apex/' + selector.xpath(
                    "//td[contains(@headers,'LINK')]/a/@href"
                ).extract_first(),
                state=selector.xpath(
                    "//td[contains(@headers,'STATE')]/text()"
                ).extract_first(),
                reg_num=selector.xpath(
                    "//td[contains(@headers,'REG_NUMBER')]/text()"
                ).extract_first(),
                address=selector.xpath(
                    "//td[contains(@headers,'ADDRESS_1')]/text()"
                ).extract_first().replace(u'\xa0', u' ').strip(),
                foreign_principal=selector.xpath(
                    "//td[contains(@headers,'FP_NAME')]/text()"
                ).extract_first(),
                date=parse(selector.xpath(
                    "//td[contains(@headers,'REG_DATE')]/text()"
                ).extract_first()).isoformat() + 'Z',
                registrant=selector.xpath(
                    "//td[contains(@headers,'REGISTRANT_NAME')]/text()"
                ).extract_first()
            )
            request = scrapy.Request(
                foreign_principal['url'],
                callback=self.get_foreign_principal_exhibit_and_country
            )
            request.meta['item'] = foreign_principal
            yield request

    def get_foreign_principal_exhibit_and_country(self, response):
        selector = scrapy.Selector(response=response)
        foreign_principal = response.meta['item']
        foreign_principal['country'] = selector.xpath(
            "//input[@id='P200_COUNTRY']/@value"
        ).extract_first()
        foreign_principal['exhibit_url'] = selector.xpath(
            "//td[@headers='DOCLINK']/a/@href"
        ).extract_first()
        return foreign_principal
